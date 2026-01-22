from typing import List, Optional
import time
import asyncio
import logging
from datetime import datetime

from app.models.domain import TypedClaim, ClaimType
from app.models.evidence import EvidenceCollection, EvidenceType, EvidenceItem, Verdict, Stance
from app.services.evidence.known_misinfo_checker import KnownMisinfoChecker
from app.services.evidence.wikidata_verifier import WikidataVerifier
from app.services.evidence.google_factcheck import GoogleFactCheck
from app.services.investigation.strategies.factory import StrategyFactory
from app.services.investigation.strategies.base import InvestigationContext, InvestigationDepth

logger = logging.getLogger(__name__)

class InvestigationOrchestrator:
    """
    Orchestrates the investigation process.
    Phase 1: Quick Checks (Databases, Fact Check API)
    Phase 2: Deep Investigation (Strategy Pattern)
    """
    
    def __init__(self):
        # Quick Check Tools
        self.misinfo_checker = KnownMisinfoChecker()
        self.wikidata_verifier = WikidataVerifier()
        self.google_factchecker = GoogleFactCheck()

    async def investigate(self, claim: TypedClaim) -> EvidenceCollection:
        """
        Run the full investigation pipeline.
        """
        start_time = time.time()
        evidence = EvidenceCollection()
        
        logger.info(f"Starting investigation for: '{claim.text}' ({claim.claim_type})")
        
        # PHASE 1: Quick Checks (Fast, cheap, authoritative)
        # Check internal database first
        misinfo_match = self.misinfo_checker.check(claim.text)
        if misinfo_match and misinfo_match.matched:
            logger.info("Found in misinfo database.")
            evidence.add(EvidenceItem(
                text=f"Known misinformation: {misinfo_match.reason}",
                source_url="internal_db",
                source_domain="FullFact/Snopes DB",
                source_type=EvidenceType.KNOWN_MISINFO,
                stance=Stance.REFUTES if misinfo_match.verdict == "VERIFIED_FALSE" else Stance.NEUTRAL,
                stance_confidence=misinfo_match.confidence,
                trust_score=100
            ))
            evidence.override_verdict = Verdict.VERIFIED_FALSE # Usually misinfo DB only stores false stuff
            evidence.override_reason = misinfo_match.reason
            self._finalize(evidence, start_time)
            return evidence
            
        # Check Wikidata (for factual claims)
        if claim.claim_type == ClaimType.FACTUAL_STATEMENT:
            wiki_result = await self.wikidata_verifier.quick_fact_check(claim.text)
            if wiki_result and wiki_result.verified is not None:
                logger.info("Verified via Wikidata.")
                stance = Stance.SUPPORTS if wiki_result.verified else Stance.REFUTES
                evidence.add(EvidenceItem(
                    text=f"Wikidata verification: {wiki_result.reason} (Actual: {wiki_result.actual_value})",
                    source_url=f"https://www.wikidata.org/wiki/{wiki_result.entity_id}" if wiki_result.entity_id else "wikidata",
                    source_domain="wikidata.org",
                    source_type=EvidenceType.WIKIDATA,
                    stance=stance,
                    stance_confidence=1.0,
                    trust_score=100
                ))
                evidence.override_verdict = Verdict.VERIFIED_TRUE if wiki_result.verified else Verdict.VERIFIED_FALSE
                evidence.override_reason = wiki_result.reason
                self._finalize(evidence, start_time)
                return evidence
                
        # Check Google Fact Check API
        fact_checks = await self.google_factchecker.search(claim.text)
        if fact_checks:
            for fc in fact_checks[:3]: # Limit to top 3
                review = fc.get("claimReview", [{}])[0]
                publisher = review.get("publisher", {}).get("name", "Unknown")
                url = review.get("url", "")
                rating = review.get("textualRating", "Unknown")
                
                # Simple mapping for MVP - ideally use the helper from factcheck.py
                stance = Stance.NEUTRAL
                if "false" in rating.lower(): stance = Stance.REFUTES
                elif "true" in rating.lower(): stance = Stance.SUPPORTS
                
                evidence.add(EvidenceItem(
                    text=f"Fact Check by {publisher}: {rating}",
                    source_url=url,
                    source_domain=publisher,
                    source_type=EvidenceType.FACT_CHECK,
                    stance=stance,
                    stance_confidence=0.95,
                    trust_score=100
                ))
        
        # If we found a definitive Fact Check, we might want to stop early?
        
        # If we found a definitive Fact Check, we might want to stop early?
        # TruthLens philosophy: "Show me the evidence". 
        # But if a professional check exists, it's strong.
        # Let's keep going for context unless we want to save API calls.
        # For now, we continue to Phase 2 to get "Fresh" context if possible, 
        # unless confidence is extremely high.
        # Logic: If we have a FACT_CHECK item with >0.9 confidence, we could stop.
        for item in evidence.items:
            if item.source_type == EvidenceType.FACT_CHECK and item.stance_confidence > 0.9:
                 logger.info("Definitive fact check found. Stopping early.")
                 # Set override verdict to match the fact check
                 if item.stance == Stance.SUPPORTS:
                     evidence.override_verdict = Verdict.VERIFIED_TRUE
                     evidence.override_reason = "Verified by professional fact-checker."
                 elif item.stance == Stance.REFUTES:
                     evidence.override_verdict = Verdict.VERIFIED_FALSE
                     evidence.override_reason = "Debunked by professional fact-checker."
                 
                 evidence.override_confidence = item.stance_confidence
                 self._finalize(evidence, start_time)
                 return evidence

        # PHASE 2: Deep Search (Strategy Pattern)
        try:
            # 1. Select Strategy
            strategy_cls = StrategyFactory.get_strategy(claim.claim_type)
            strategy = strategy_cls()
            
            # 2. Create Context
            # We enforce deep search by default in this phase
            ctx = InvestigationContext(
                claim=claim,
                timestamp=datetime.now(),
                required_depth=InvestigationDepth.DEEP,
                known_evidence=evidence # Pass existing evidence (e.g. fact checks)
            )
            
            # 3. Execute with Timeout
            # Global timeout for deep search
            logger.info(f"Executing strategy: {strategy_cls.__name__}")
            
            investigation_result = await asyncio.wait_for(
                strategy.execute(ctx),
                timeout=45.0
            )
            
            # 4. Merge Results
            evidence.items.extend(investigation_result.evidence.items)
            evidence.sources_checked += len(investigation_result.evidence.items) # Count items as sources roughly, or use strategy stats if available
            # Better: use the sources_checked from inner evidence if tracked, but strategies might just return items
            # strategies usually return InvestigationResult which has 'evidence' (EvidenceCollection)
            # So we should sum it up.
            evidence.sources_checked += investigation_result.evidence.sources_checked
            
            # Propagate Strategy Decision
            # CRITICAL FIX: Respect high-confidence results from strategy, even if they are UNVERIFIED/DISPUTED.
            # Don't let the synthesizer override a specific strategy finding.
            if investigation_result.verdict != Verdict.UNVERIFIED or investigation_result.confidence_score > 0.6:
                evidence.override_verdict = investigation_result.verdict
                evidence.override_confidence = investigation_result.confidence_score
                evidence.override_reason = investigation_result.reason
                
            # Copy strategy stats
            evidence.strategy_stats = investigation_result.strategy_stats
                
        except asyncio.TimeoutError:
            logger.error("Deep investigation timed out.")
            evidence.stop_reason = "timeout"
            
        except Exception as e:
            logger.error(f"Strategy execution failed: {e}", exc_info=True)
            # We don't crash, we return partial evidence
            
        self._finalize(evidence, start_time)
        return evidence
        
    def _finalize(self, evidence: EvidenceCollection, start_time: float):
        """Finalize stats."""
        evidence.investigation_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Investigation completed in {evidence.investigation_time_ms}ms. Sources: {evidence.sources_checked}")


# Singleton instance
_orchestrator_instance = None

def get_orchestrator() -> InvestigationOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = InvestigationOrchestrator()
    return _orchestrator_instance
