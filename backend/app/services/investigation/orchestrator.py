"""
Investigation Orchestrator

Coordinates the multi-step investigation process.
Phase 2B: Async parallel execution with time bounds.
"""

import time
import asyncio
from typing import List, Optional
from datetime import datetime
from urllib.parse import urlparse

from app.models.evidence import (
    EvidenceItem, EvidenceCollection, EvidenceType, Stance
)
from app.models.domain import TypedClaim, ClaimType
from app.services.evidence import (
    get_wikidata_verifier, 
    get_misinfo_checker,
    get_trust_scorer,
    get_google_factcheck
)
from app.services.investigation.searchers import (
    get_duckduckgo_searcher,
    get_wikipedia_searcher
)
# Deep Searchers
from app.services.investigation.searchers.pubmed import PubMedSearcher
from app.services.investigation.searchers.archive import ArchiveOrgSearcher


class InvestigationOrchestrator:
    """
    Orchestrate the evidence gathering process (Async).
    
    Phase 2B Strategy:
    1. Quick Check (Misinfo + Wikidata) -> Await first.
       If definitive result found, STOP.
    2. Deep Search (DuckDuckGo + Wikipedia + PubMed/Archive) -> Run in PARALLEL.
       Enforce global timeout (45s).
       - specialized searchers triggered by ClaimType.
    
    Usage:
        orchestrator = get_orchestrator()
        evidence = await orchestrator.investigate(typed_claim)
    """
    
    def __init__(self):
        # Initialize all searchers/verifiers
        self.misinfo_checker = get_misinfo_checker()
        self.wikidata_verifier = get_wikidata_verifier()
        self.ddg_searcher = get_duckduckgo_searcher()
        self.wiki_searcher = get_wikipedia_searcher()
        self.trust_scorer = get_trust_scorer()
        self.google_factcheck = get_google_factcheck()
        
        # Deep Searchers (instantiated here for now, could be singleton)
        self.pubmed_searcher = PubMedSearcher()
        self.archive_searcher = ArchiveOrgSearcher()
    
    async def investigate(self, claim: TypedClaim) -> EvidenceCollection:
        """
        Perform full investigation on a claim (Async).
        """
        start_time = time.time()
        evidence = EvidenceCollection()
        
        # Skip investigation for non-checkable claims
        if not claim.is_checkable:
            evidence.investigation_time_ms = int((time.time() - start_time) * 1000)
            return evidence
        
        try:
            # PHASE 1: Quick Checks (Sequential/Fast)
            # ---------------------------------------
            
            # 1. Check known misinformation database (Sync is fine, it's fast regex/dict)
            self._check_known_misinfo(claim.text, evidence)
            if evidence.stopped_early:
                 evidence.investigation_time_ms = int((time.time() - start_time) * 1000)
                 return evidence
            
            # 2. Wikidata verification (Async)
            # Only for FACTUAL claims
            if claim.claim_type == ClaimType.FACTUAL_STATEMENT:
                await self._verify_wikidata(claim.text, evidence)
            
            # 3. Google Fact Check API
            await self._check_google_factcheck(claim.text, evidence)
            if evidence.stopped_early:
                 evidence.investigation_time_ms = int((time.time() - start_time) * 1000)
                 return evidence
            
            # PHASE 2: Deep Search (Parallel/Async)
            # -------------------------------------
            
            # Run DuckDuckGo, Wikipedia, and Specialized Searchers in parallel
            # We wrap this in wait_for to enforce global timeout
            try:
                await asyncio.wait_for(
                    self._run_parallel_searches(claim, evidence),
                    timeout=45.0
                )
            except asyncio.TimeoutError:
                print("Investigation timed out after 45s.")
                evidence.stop_reason = "timeout"
            
        except Exception as e:
            print(f"Investigation error: {e}")
        
        # Calculate investigation time
        evidence.investigation_time_ms = int((time.time() - start_time) * 1000)
        
        return evidence

    async def _run_parallel_searches(self, claim: TypedClaim, evidence: EvidenceCollection):
        """Run web searches in parallel."""
        tasks = []
        
        # Standard Searchers (Always run)
        tasks.append(asyncio.create_task(self._search_duckduckgo(claim.text, evidence)))
        tasks.append(asyncio.create_task(self._search_wikipedia(claim.text, evidence)))
        
        # Specialized Searchers (Conditional)
        if claim.claim_type == ClaimType.SCIENTIFIC_MEDICAL:
            print(f"🔬 Triggering PubMed Search for: {claim.text}")
            tasks.append(asyncio.create_task(self._search_pubmed(claim.text, evidence)))
            
        # Archive.org search (Trigger for Factual/Political as per Phase 2 doc)
        if claim.claim_type in [ClaimType.FACTUAL_STATEMENT, ClaimType.POLITICAL_ALLEGATION]:
            print(f"🏛️ Triggering Archive.org Search for: {claim.text}")
            tasks.append(asyncio.create_task(self._search_archive(claim, evidence)))

        # Wait for all to complete
        await asyncio.gather(*tasks)
    
    def _check_known_misinfo(self, claim_text: str, evidence: EvidenceCollection):
        """Check against known misinformation database."""
        try:
            result = self.misinfo_checker.check(claim_text)
            if result and result.matched:
                evidence.add(EvidenceItem(
                    text=result.reason,
                    source_url="internal://known_misinformation_db",
                    source_domain="truthlens.local",
                    source_type=EvidenceType.KNOWN_MISINFO,
                    stance=Stance.REFUTES,  # Known misinfo = refutes
                    stance_confidence=result.confidence,
                    trust_score=100  # Our own database
                ))
                evidence.sources_checked += 1
                evidence.stopped_early = True
                evidence.stop_reason = "known_misinfo"
        except Exception as e:
            print(f"Misinfo check error: {e}")
    
    async def _verify_wikidata(self, claim_text: str, evidence: EvidenceCollection):
        """Verify factual claim against Wikidata (Async)."""
        try:
            result = await self.wikidata_verifier.quick_fact_check(claim_text)
            if result and result.verified is not None:
                stance = Stance.SUPPORTS if result.verified else Stance.REFUTES
                evidence.add(EvidenceItem(
                    text=f"Wikidata verification: claimed '{result.claimed_value}', "
                         f"actual '{result.actual_value}'. {result.reason}",
                    source_url=f"https://www.wikidata.org/wiki/{result.entity_id}" 
                               if result.entity_id else "https://www.wikidata.org",
                    source_domain="wikidata.org",
                    source_type=EvidenceType.WIKIDATA,
                    stance=stance,
                    stance_confidence=0.9 if result.verified is not None else 0.5,
                    trust_score=85
                ))
                evidence.sources_checked += 1
        except Exception as e:
            print(f"Wikidata verification error: {e}")
    
    async def _search_duckduckgo(self, claim_text: str, evidence: EvidenceCollection):
        """Search DuckDuckGo (Async)."""
        try:
            # Strategy 1: Specific "fact check" search
            search_query = f"{claim_text} fact check"
            results = await self.ddg_searcher.search(search_query, max_results=3)
            
            # Strategy 2: Fallback to general search if no results
            if not results:
                print(f"No results for '{search_query}', falling back to general search...")
                results = await self.ddg_searcher.search(claim_text, max_results=5)
            
            for result in results:
                if len(result.snippet) < 50: continue
                    
                trust_score, _ = self.trust_scorer.get_trust_score(result.source_domain)
                
                evidence.add(EvidenceItem(
                    text=result.snippet,
                    source_url=result.url,
                    source_domain=result.source_domain,
                    source_type=EvidenceType.WEB_SEARCH, 
                    stance=Stance.NEUTRAL,  # Will be analyzed by synthesizer (RoBERTa)
                    stance_confidence=0.0,  # Reset to 0 to force ML check
                    trust_score=trust_score
                ))
                evidence.sources_checked += 1
                
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
    
    async def _search_wikipedia(self, claim_text: str, evidence: EvidenceCollection):
        """Search Wikipedia (Async)."""
        try:
            results = await self.wiki_searcher.get_extract_for_claim(claim_text, max_articles=2)
            for result in results:
                evidence.add(EvidenceItem(
                    text=result.extract,
                    source_url=result.url,
                    source_domain="wikipedia.org",
                    source_type=EvidenceType.WIKIPEDIA,
                    stance=Stance.NEUTRAL,
                    stance_confidence=0.0, # Force ML check
                    trust_score=85         # Wikipedia is generally trusted/neutral
                ))
                evidence.sources_checked += 1
        except Exception as e:
            print(f"Wikipedia search error: {e}")

    async def _search_pubmed(self, claim_text: str, evidence: EvidenceCollection):
        """Search PubMed (Async)."""
        try:
            results = await self.pubmed_searcher.search(claim_text, max_results=3)
            for result in results:
                evidence.add(EvidenceItem(
                    text=result.snippet,
                    source_url=result.url,
                    source_domain=result.source_domain,
                    source_type=EvidenceType.ACADEMIC_PAPER,
                    stance=Stance.NEUTRAL,
                    stance_confidence=0.0,
                    trust_score=95
                ))
        except Exception as e:
            print(f"PubMed search error: {e}")

    async def _check_google_factcheck(self, claim_text: str, evidence: EvidenceCollection):
        """Check Google Fact Check API."""
        try:
            claims = await self.google_factcheck.search(claim_text)
            for claim in claims:
                for check in claim.get("claimReview", []):
                    title = check.get("title", "")
                    rating = check.get("textualRating", "").lower()
                    
                    # Map rating to stance
                    stance = Stance.NEUTRAL
                    if any(w in rating for w in ["false", "incorrect", "debunked", "misleading"]):
                        stance = Stance.REFUTES
                    elif any(w in rating for w in ["true", "correct", "accurate"]):
                        stance = Stance.SUPPORTS
                        
                    evidence.add(EvidenceItem(
                        text=f"Fact Check: {title} - Rating: {rating}",
                        source_url=check.get("url", ""),
                        source_domain=urlparse(check.get("url", "")).netloc.replace("www.", "") if check.get("url") else "factcheck.google",
                        source_type=EvidenceType.GOOGLE_FACT_CHECK,
                        stance=stance,
                        stance_confidence=1.0 if stance != Stance.NEUTRAL else 0.5,
                        trust_score=95
                    ))
                    
                    # Stop early if we have a definitive fact check
                    if stance != Stance.NEUTRAL:
                        evidence.stopped_early = True
                        evidence.stop_reason = "definitive_fact_check"
        except Exception as e:
            print(f"Google Fact Check error: {e}")

    async def _search_archive(self, claim: TypedClaim, evidence: EvidenceCollection):
        """Search Archive.org for history."""
        try:
            # We check the claim text as a query
            results = await self.archive_searcher.search(claim.text, max_results=2)
            for result in results:
                evidence.add(EvidenceItem(
                    text=result.snippet,
                    source_url=result.url,
                    source_domain="archive.org",
                    source_type=EvidenceType.ARCHIVE,
                    stance=Stance.NEUTRAL,
                    stance_confidence=0.0,
                    trust_score=80
                ))
        except Exception as e:
            print(f"Archive.org search error: {e}")


# Singleton instance
_orchestrator_instance: Optional[InvestigationOrchestrator] = None


def get_orchestrator() -> InvestigationOrchestrator:
    """Get singleton instance of InvestigationOrchestrator."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = InvestigationOrchestrator()
    return _orchestrator_instance
