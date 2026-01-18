"""
Evidence Synthesizer

Analyzes evidence stance and synthesizes into verdict.
Phase 2A: Keyword-based stance detection (sync).
Phase 2B: Will add RoBERTa model.
"""

import re
from typing import List, Tuple
from app.models.evidence import (
    EvidenceItem, EvidenceCollection, Stance, Verdict,
    EvidenceType
)
from app.services.evidence.source_trust import get_trust_scorer


class EvidenceSynthesizer:
    """
    Synthesize evidence into a verdict.
    
    Phase 2A uses keyword-based stance detection.
    Phase 2B will integrate RoBERTa-large-mnli.
    
    Usage:
        synthesizer = EvidenceSynthesizer()
        verdict, confidence, summary = synthesizer.synthesize(evidence, claim)
    """
    
    # Keywords indicating refutation/false claim
    REFUTE_KEYWORDS = [
        "false", "fake", "hoax", "debunked", "myth", "misleading",
        "incorrect", "not true", "no evidence", "disproven", "wrong",
        "misinformation", "disinformation", "fact check: false",
        "rated false", "pants on fire", "no scientific evidence",
        "conspiracy", "unsubstantiated", "baseless", "unfounded",
        "claim is false", "no proof", "not accurate", "fraud",
        "scam", "pseudoscientific", "refuted", "denies", "denied"
    ]
    
    # Keywords indicating support/true claim
    SUPPORT_KEYWORDS = [
        "true", "verified", "confirmed", "accurate", "correct",
        "fact check: true", "rated true", "evidence shows",
        "studies confirm", "research supports", "proven",
        "scientifically proven", "experts confirm", "data shows",
        "officially confirmed", "established fact",
        "found that", "concluded", "demonstrates", "linked to",
        "associated with", "responsible for", "won the",
        "is the", "was the", "located in", "born in",
        "causes", "cause of", "leads to", "result of",
        "resulted in", "due to", "because of"
    ]
    
    # Keywords indicating mixed/disputed status
    DISPUTE_KEYWORDS = [
        "disputed", "controversial", "mixed", "partly true",
        "half true", "mostly false", "lacks context", "misleading",
        "out of context", "exaggerated", "more context needed",
        "debated", "unclear", "inconclusive", "conflicting"
    ]
    
    def __init__(self):
        self.trust_scorer = get_trust_scorer()
    
    def detect_stance(self, evidence_text: str, claim_text: str) -> Tuple[Stance, float]:
        """
        Detect the stance of evidence relative to a claim.
        
        Phase 2A: Keyword-based approach.
        
        Args:
            evidence_text: The evidence snippet
            claim_text: The original claim
            
        Returns:
            (Stance, confidence)
        """
        text_lower = evidence_text.lower()
        
        # Count keyword matches
        refute_count = sum(1 for kw in self.REFUTE_KEYWORDS if kw in text_lower)
        support_count = sum(1 for kw in self.SUPPORT_KEYWORDS if kw in text_lower)
        dispute_count = sum(1 for kw in self.DISPUTE_KEYWORDS if kw in text_lower)
        
        # Determine stance based on keyword counts
        if refute_count > support_count and refute_count > 0:
            confidence = min(0.5 + (refute_count * 0.1), 0.9)
            return Stance.REFUTES, confidence
        
        elif support_count > refute_count and support_count > 0:
            confidence = min(0.5 + (support_count * 0.1), 0.9)
            return Stance.SUPPORTS, confidence
        
        elif dispute_count > 0:
            return Stance.NEUTRAL, 0.5
        
        # Default: neutral with low confidence
        return Stance.NEUTRAL, 0.3
    
    def synthesize(
        self, 
        evidence: EvidenceCollection, 
        claim_text: str
    ) -> Tuple[Verdict, float, str]:
        """
        Synthesize all evidence into a verdict.
        
        Args:
            evidence: Collection of evidence items
            claim_text: The original claim
            
        Returns:
            (Verdict, confidence, summary)
        """
        if not evidence.items:
            return (
                Verdict.INSUFFICIENT_EVIDENCE,
                0.0,
                "No evidence found to verify this claim."
            )
        
        # Process each evidence item to detect stance if not already set
        for item in evidence.items:
            if item.stance == Stance.NEUTRAL and item.stance_confidence <= 0.5:
                stance, conf = self.detect_stance(item.text, claim_text)
                item.stance = stance
                item.stance_confidence = conf
        
        # Calculate weighted scores
        support_score = evidence.support_score
        refute_score = evidence.refute_score
        total_score = support_score + refute_score
        
        # Count by stance
        support_count = len([e for e in evidence.items if e.stance == Stance.SUPPORTS])
        refute_count = len([e for e in evidence.items if e.stance == Stance.REFUTES])
        neutral_count = len([e for e in evidence.items if e.stance == Stance.NEUTRAL])
        
        # Determine verdict
        verdict, confidence = self._determine_verdict(
            support_score, refute_score, total_score,
            support_count, refute_count, neutral_count,
            len(evidence.items),
            evidence.items  # Pass items for authoritative check
        )
        
        # Generate summary
        summary = self._generate_summary(
            verdict, confidence,
            support_count, refute_count, neutral_count,
            evidence.items
        )
        
        return verdict, confidence, summary
    
    def _determine_verdict(
        self,
        support_score: float,
        refute_score: float,
        total_score: float,
        support_count: int,
        refute_count: int,
        neutral_count: int,
        total_count: int,
        items: List[EvidenceItem] = None
    ) -> Tuple[Verdict, float]:
        """
        Determine verdict based on evidence scores.
        
        Logic:
        - Check for authoritative sources first (known_misinfo, wikidata, fact_check)
        - VERIFIED_FALSE if refute_score > support_score * 1.5
        - VERIFIED_TRUE if support_score > refute_score * 1.5
        - INSUFFICIENT_EVIDENCE if < 2 pieces of evidence AND no authoritative
        - DISPUTED otherwise
        """
        items = items or []
        
        # Check for authoritative sources (these are decisive on their own)
        authoritative_types = {
            EvidenceType.KNOWN_MISINFO,
            EvidenceType.WIKIDATA,
            EvidenceType.FACT_CHECK
        }
        
        for item in items:
            if item.source_type in authoritative_types:
                if item.stance == Stance.REFUTES:
                    return Verdict.VERIFIED_FALSE, max(item.stance_confidence, 0.85)
                elif item.stance == Stance.SUPPORTS:
                    return Verdict.VERIFIED_TRUE, max(item.stance_confidence, 0.85)
        
        # Not enough evidence (and no authoritative source)
        if total_count < 2:
            return Verdict.INSUFFICIENT_EVIDENCE, 0.2
        
        if total_score == 0:
            return Verdict.UNVERIFIED, 0.3
        
        # Strong refutation
        if refute_score > support_score * 1.5 and refute_count >= 1:
            confidence = min(refute_score / (total_score + 0.1), 0.95)
            return Verdict.VERIFIED_FALSE, confidence
        
        # Strong support
        if support_score > refute_score * 1.5 and support_count >= 1:
            confidence = min(support_score / (total_score + 0.1), 0.95)
            return Verdict.VERIFIED_TRUE, confidence
        
        # All neutral
        if neutral_count == total_count:
            return Verdict.UNVERIFIED, 0.4
        
        # Mixed evidence - disputed
        diff = abs(support_score - refute_score)
        confidence = max(0.3, 1 - (diff / (total_score + 0.1)))
        return Verdict.DISPUTED, confidence
    
    def _generate_summary(
        self,
        verdict: Verdict,
        confidence: float,
        support_count: int,
        refute_count: int,
        neutral_count: int,
        items: List[EvidenceItem]
    ) -> str:
        """Generate human-readable summary of evidence synthesis."""
        total = support_count + refute_count + neutral_count
        
        # Get top sources
        top_sources = []
        for item in items[:3]:
            if item.source_domain not in top_sources:
                top_sources.append(item.source_domain)
        
        sources_str = ", ".join(top_sources) if top_sources else "various sources"
        
        summaries = {
            Verdict.VERIFIED_FALSE: (
                f"Analysis of {total} sources ({sources_str}) indicates this claim "
                f"is FALSE. {refute_count} source(s) refute the claim."
            ),
            Verdict.VERIFIED_TRUE: (
                f"Analysis of {total} sources ({sources_str}) supports this claim "
                f"as TRUE. {support_count} source(s) confirm the claim."
            ),
            Verdict.DISPUTED: (
                f"This claim is DISPUTED. Of {total} sources checked, "
                f"{support_count} support and {refute_count} refute the claim."
            ),
            Verdict.INSUFFICIENT_EVIDENCE: (
                f"Insufficient evidence to verify this claim. "
                f"Only {total} source(s) found with limited stance information."
            ),
            Verdict.UNVERIFIED: (
                f"Could not verify this claim. {total} sources found but "
                f"no clear stance detected."
            ),
            Verdict.NOT_CHECKABLE: (
                "This claim type cannot be fact-checked (e.g., opinion, prediction)."
            )
        }
        
        return summaries.get(verdict, "Unable to determine claim status.")


# Singleton instance
_synthesizer_instance = None


def get_synthesizer() -> EvidenceSynthesizer:
    """Get singleton instance of EvidenceSynthesizer."""
    global _synthesizer_instance
    if _synthesizer_instance is None:
        _synthesizer_instance = EvidenceSynthesizer()
    return _synthesizer_instance
