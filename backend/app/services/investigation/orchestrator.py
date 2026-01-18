"""
Investigation Orchestrator

Coordinates the multi-step investigation process.
Phase 2A: Synchronous, sequential execution.
Phase 2B: Will add async parallel execution with time bounds.
"""

import time
from typing import List, Optional
from datetime import datetime

from app.models.evidence import (
    EvidenceItem, EvidenceCollection, EvidenceType, Stance
)
from app.models.domain import TypedClaim, ClaimType
from app.services.evidence import (
    get_wikidata_verifier, 
    get_misinfo_checker,
    get_trust_scorer
)
from app.services.investigation.searchers import (
    get_duckduckgo_searcher,
    get_wikipedia_searcher
)


class InvestigationOrchestrator:
    """
    Orchestrate the evidence gathering process.
    
    Phase 2A runs all steps sequentially (sync).
    Phase 2B will run steps in parallel with time bounds.
    
    Investigation Steps:
    1. Known misinformation check (instant)
    2. Wikidata verification (for factual claims)
    3. DuckDuckGo web search
    4. Wikipedia lookup
    
    Usage:
        orchestrator = InvestigationOrchestrator()
        evidence = orchestrator.investigate(typed_claim)
    """
    
    def __init__(self):
        # Initialize all searchers/verifiers
        self.misinfo_checker = get_misinfo_checker()
        self.wikidata_verifier = get_wikidata_verifier()
        self.ddg_searcher = get_duckduckgo_searcher()
        self.wiki_searcher = get_wikipedia_searcher()
        self.trust_scorer = get_trust_scorer()
    
    def investigate(self, claim: TypedClaim) -> EvidenceCollection:
        """
        Perform full investigation on a claim.
        
        Args:
            claim: TypedClaim from Phase 1
            
        Returns:
            EvidenceCollection with all gathered evidence
        """
        start_time = time.time()
        evidence = EvidenceCollection()
        
        # Skip investigation for non-checkable claims
        if not claim.is_checkable:
            evidence.investigation_time_ms = int((time.time() - start_time) * 1000)
            return evidence
        
        # Step 1: Check known misinformation database
        self._check_known_misinfo(claim.text, evidence)
        
        # Step 2: Wikidata verification (for FACTUAL claims)
        if claim.claim_type == ClaimType.FACTUAL_STATEMENT:
            self._verify_wikidata(claim.text, evidence)
        
        # Step 3: DuckDuckGo web search
        self._search_duckduckgo(claim.text, evidence)
        
        # Step 4: Wikipedia lookup
        self._search_wikipedia(claim.text, evidence)
        
        # Calculate investigation time
        evidence.investigation_time_ms = int((time.time() - start_time) * 1000)
        
        return evidence
    
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
        except Exception as e:
            print(f"Misinfo check error: {e}")
    
    def _verify_wikidata(self, claim_text: str, evidence: EvidenceCollection):
        """Verify factual claim against Wikidata."""
        try:
            result = self.wikidata_verifier.quick_fact_check(claim_text)
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
    
    def _search_duckduckgo(self, claim_text: str, evidence: EvidenceCollection):
        """Search DuckDuckGo for relevant content."""
        try:
            # Strategy 1: Specific "fact check" search
            search_query = f"{claim_text} fact check"
            results = self.ddg_searcher.search(search_query, max_results=3)
            
            # Strategy 2: Fallback to general search if no results
            if not results:
                print(f"No results for '{search_query}', falling back to general search...")
                results = self.ddg_searcher.search(claim_text, max_results=5)
            
            for result in results:
                # Skip if snippet is too short
                if len(result.snippet) < 50:
                    continue
                    
                trust_score, _ = self.trust_scorer.get_trust_score(result.source_domain)
                
                evidence.add(EvidenceItem(
                    text=result.snippet,
                    source_url=result.url,
                    source_domain=result.source_domain,
                    source_type=EvidenceType.WEB_SEARCH,
                    stance=Stance.NEUTRAL,  # Will be analyzed by synthesizer
                    stance_confidence=0.3,
                    trust_score=trust_score
                ))
                evidence.sources_checked += 1
                
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
    
    def _search_wikipedia(self, claim_text: str, evidence: EvidenceCollection):
        """Search Wikipedia for relevant articles."""
        try:
            # Get relevant article summaries
            results = self.wiki_searcher.get_extract_for_claim(claim_text, max_articles=2)
            
            for result in results:
                evidence.add(EvidenceItem(
                    text=result.extract,
                    source_url=result.url,
                    source_domain="wikipedia.org",
                    source_type=EvidenceType.WIKIPEDIA,
                    stance=Stance.NEUTRAL,  # Will be analyzed by synthesizer
                    stance_confidence=0.3,
                    trust_score=75
                ))
                evidence.sources_checked += 1
                
        except Exception as e:
            print(f"Wikipedia search error: {e}")


# Singleton instance
_orchestrator_instance: Optional[InvestigationOrchestrator] = None


def get_orchestrator() -> InvestigationOrchestrator:
    """Get singleton instance of InvestigationOrchestrator."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = InvestigationOrchestrator()
    return _orchestrator_instance
