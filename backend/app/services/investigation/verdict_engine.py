"""
Verdict Engine

Final verdict determination based on synthesized evidence.
Phase 2A: Synchronous implementation.

CRITICAL: LLM is NEVER used for verdict. Evidence determines verdict.
"""

from typing import Optional
from datetime import datetime

from app.models.evidence import (
    EvidenceCollection, VerifiedClaim, Verdict
)
from app.models.domain import TypedClaim, ClaimType
from app.services.investigation.synthesizer import get_synthesizer
from app.services.investigation.orchestrator import get_orchestrator
from app.services.investigation.explanation import get_explanation_service


class VerdictEngine:
    """
    Determine final verdict for a claim.
    
    This is the main entry point for Phase 2 investigation.
    
    IMPORTANT: The verdict is determined ENTIRELY by evidence.
    LLM is NEVER used for verdict determination.
    (LLM will be added in Phase 4 for explanation generation only)
    
    Usage:
        engine = VerdictEngine()
        result = engine.verify(typed_claim)
        print(result.verdict, result.confidence)
    """
    
    def __init__(self):
        self.orchestrator = get_orchestrator()
        self.synthesizer = get_synthesizer()
        self.explanation_service = get_explanation_service()
    
    async def verify(self, claim: TypedClaim) -> VerifiedClaim:
        """
        Verify a claim and return verdict with evidence (Async).
        
        Args:
            claim: TypedClaim from Phase 1 (claim extraction + typing)
            
        Returns:
            VerifiedClaim with verdict, confidence, and evidence trail
        """
        # Handle non-checkable claims immediately
        if not claim.is_checkable:
            return self._create_not_checkable_result(claim)
        
        # Gather evidence (Async)
        evidence = await self.orchestrator.investigate(claim)
        
        if not evidence.items and not evidence.override_verdict:
            return VerifiedClaim(
                original_text=claim.text,
                claim_type=claim.claim_type.value,
                verdict=Verdict.INSUFFICIENT_EVIDENCE,
                confidence=0.0,
                evidence_summary="No evidence could be gathered for this claim.",
                evidence_items=[],
                investigation_time_ms=evidence.investigation_time_ms,
                sources_checked=evidence.sources_checked
            )
        
        # Check for Strategy Override (Phase 3)
        if evidence.override_verdict:
            # Map string verdict back to Enum if needed, usually it is Enum value
            try:
                final_verdict = Verdict(evidence.override_verdict)
            except ValueError:
                final_verdict = Verdict.UNVERIFIED
            
            verified_claim = VerifiedClaim(
                original_text=claim.text,
                claim_type=claim.claim_type.value,
                verdict=final_verdict,
                confidence=evidence.override_confidence or 0.0,
                evidence_summary=evidence.override_reason or "Verdict determined by specialized strategy.",
                evidence_items=evidence.items,
                investigation_time_ms=evidence.investigation_time_ms,
                sources_checked=evidence.sources_checked,
                strategy_stats=evidence.strategy_stats
            )
            
            # Enrich override verdict too
            try:
                enriched_summary = await self.explanation_service.generate_explanation(verified_claim)
                verified_claim.evidence_summary = enriched_summary
            except Exception as e:
                print(f"Explanation enrichment failed: {e}")
                
            return verified_claim
            
        # Synthesize evidence into verdict (Sync is fine, it's fast CPU work)
        # UPDATE: It is NOT fast if ML is involved. Use threadpool to avoid blocking loop.
        from fastapi.concurrency import run_in_threadpool
        
        verdict, confidence, summary = await run_in_threadpool(
            self.synthesizer.synthesize,
            evidence, 
            claim.text
        )
        
        # Baseline VerifiedClaim
        verified_claim = VerifiedClaim(
            original_text=claim.text,
            claim_type=claim.claim_type.value,
            verdict=verdict,
            confidence=confidence,
            evidence_summary=summary,
            evidence_items=evidence.items,
            investigation_time_ms=evidence.investigation_time_ms,
            sources_checked=evidence.sources_checked,
            strategy_stats=evidence.strategy_stats
        )

        # PHASE 4: LLM Explanation Enrichment
        # This replaces the robotic synthesizer summary with human-readable text
        try:
            enriched_summary = await self.explanation_service.generate_explanation(verified_claim)
            verified_claim.evidence_summary = enriched_summary
        except Exception as e:
            print(f"Explanation enrichment failed: {e}")
            # Fallback to original summary if LLM fails
        
        return verified_claim
    
    def _create_not_checkable_result(self, claim: TypedClaim) -> VerifiedClaim:
        """Create result for non-checkable claims (opinions, predictions, etc)."""
        # User-friendly explanations for each non-checkable type
        reason_map = {
            ClaimType.OPINION: "Opinions and value judgments cannot be fact-checked.",
            ClaimType.PREDICTION: "Future predictions cannot be verified until they occur.",
            ClaimType.QUESTION: "Questions are not assertions that can be verified.",
            ClaimType.COMMAND: "Commands/imperatives are not factual claims.",
            ClaimType.HYPOTHETICAL: "Hypothetical scenarios cannot be fact-checked.",
            ClaimType.UNKNOWN: "This statement type could not be classified for fact-checking.",
        }
        
        return VerifiedClaim(
            original_text=claim.text,
            claim_type=claim.claim_type.value,
            verdict=Verdict.NOT_CHECKABLE,
            confidence=1.0,  # Confident it's not checkable
            evidence_summary=reason_map.get(
                claim.claim_type, 
                "This statement cannot be fact-checked."
            ),
            evidence_items=[],
            investigation_time_ms=0,
            sources_checked=0
        )


# Singleton instance
_engine_instance: Optional[VerdictEngine] = None


def get_verdict_engine() -> VerdictEngine:
    """Get singleton instance of VerdictEngine."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = VerdictEngine()
    return _engine_instance
