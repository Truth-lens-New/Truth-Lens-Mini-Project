"""
Evidence Synthesizer

Analyzes evidence stance and synthesizes into verdict.
Phase 2B: Uses RoBERTa-large-mnli for semantic stance detection.
"""

from typing import List, Tuple
from app.models.evidence import (
    EvidenceItem, EvidenceCollection, Stance, Verdict,
    EvidenceType
)
from app.services.evidence.source_trust import get_trust_scorer
from app.services.investigation.stance_detector import StanceDetector


class EvidenceSynthesizer:
    """
    Synthesize evidence into a verdict using ML-based Stance Detection.
    
    Uses:
    1. RoBERTa-large-mnli for stance detection (Supports/Refutes/Neutral)
    2. Source Trust Scoring for weighting
    3. Weighted Voting for final verdict
    """
    
    def __init__(self):
        self.trust_scorer = get_trust_scorer()
        self.stance_detector = StanceDetector()
    
    def detect_stance(self, evidence_text: str, claim_text: str) -> Tuple[Stance, float]:
        """
        Detect the stance of evidence relative to a claim using RoBERTa.
        """
        try:
            result = self.stance_detector.detect(claim_text, evidence_text)
            
            label = result["label"]
            score = result["score"]
            
            if label == "SUPPORTS":
                return Stance.SUPPORTS, score
            elif label == "REFUTES":
                return Stance.REFUTES, score
            else:
                return Stance.NEUTRAL, score
                
        except Exception as e:
            print(f"Stance detection error: {e}")
            return Stance.NEUTRAL, 0.0
    
    def synthesize(
        self, 
        evidence: EvidenceCollection, 
        claim_text: str
    ) -> Tuple[Verdict, float, str]:
        """
        Synthesize all evidence into a verdict.
        """
        if not evidence.items:
            return (
                Verdict.INSUFFICIENT_EVIDENCE,
                0.0,
                "No evidence found to verify this claim."
            )
        
        # Process each evidence item to detect stance if not already set
        for item in evidence.items:
            # Overwrite even if set, if it's NEUTRAL (re-check with ML)? 
            # Or just check everything? 
            # Strategy: If stance is NEUTRAL/Unset, check it.
            # If it came from a source that explicitly sets stance (like FactCheck), keep it.
            if item.stance == Stance.NEUTRAL or item.stance_confidence == 0.0:
                 # Check if text is long enough
                 if len(item.text.split()) > 3:
                    stance, conf = self.detect_stance(item.text, claim_text)
                    item.stance = stance
                    item.stance_confidence = conf
        
        # Calculate weighted scores
        # We need to re-calculate scores since we updated stances
        # The EvidenceCollection might not auto-update if we modify items directly
        # But EvidenceCollection properties calculate on the fly usually? 
        # Let's check EvidenceCollection model. Assuming it's properties.
        # But we need to ensure item.source_trust_score is set.
        
        # Re-calc trust scores just in case
        # Re-calc trust scores just in case
        for item in evidence.items:
             if item.trust_score == 0:
                 item.trust_score = self.trust_scorer.get_score(item.source_domain)

        # Calculate weighted scores manually to be sure or rely on collection methods if they exist
        # EvidenceCollection usually sums them up.
        
        support_score = sum(i.weighted_score for i in evidence.items if i.stance == Stance.SUPPORTS)
        refute_score = sum(i.weighted_score for i in evidence.items if i.stance == Stance.REFUTES)
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
            evidence.items
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
        """
        items = items or []
        
        # Check for authoritative sources first (known_misinfo, wikidata, fact_check)
        authoritative_types = {
            EvidenceType.KNOWN_MISINFO,
            EvidenceType.WIKIDATA,
            EvidenceType.FACT_CHECK
        }
        
        for item in items:
            if item.source_type in authoritative_types:
                if item.stance == Stance.REFUTES:
                    return Verdict.VERIFIED_FALSE, max(item.stance_confidence, 0.90)
                elif item.stance == Stance.SUPPORTS:
                    return Verdict.VERIFIED_TRUE, max(item.stance_confidence, 0.90)
        
        # Not enough evidence
        if total_count < 2 and total_score < 0.2:
             # If we have 1 strong piece (not authoritative but high score)?
             if total_score > 0.5:
                 pass # Continue
             else:
                return Verdict.INSUFFICIENT_EVIDENCE, 0.0
        
        if total_score == 0:
            return Verdict.UNVERIFIED, 0.0
        
        # Refutation Dominant
        # If refute score is significantly higher
        if refute_score > support_score * 1.5:
             # Confidence is ratio of refute to total
             confidence = refute_score / (total_score + 0.01)
             return Verdict.VERIFIED_FALSE, min(confidence, 0.95)

        # Support Dominant
        if support_score > refute_score * 1.5:
             confidence = support_score / (total_score + 0.01)
             return Verdict.VERIFIED_TRUE, min(confidence, 0.95)
        
        # Mixed / Disputed
        return Verdict.DISPUTED, 0.5
    
    def _generate_summary(
        self,
        verdict: Verdict,
        confidence: float,
        support_count: int,
        refute_count: int,
        neutral_count: int,
        items: List[EvidenceItem]
    ) -> str:
        """Generate human-readable summary."""
        total = support_count + refute_count + neutral_count
        
        top_sources = []
        seen = set()
        for item in items:
            if item.source_domain not in seen:
                 top_sources.append(item.source_domain)
                 seen.add(item.source_domain)
            if len(top_sources) >= 3: break
        
        sources_str = ", ".join(top_sources) if top_sources else "web sources"
        
        if verdict == Verdict.VERIFIED_FALSE:
            return f"Evidence indicates this is FALSE. {refute_count} sources (including {sources_str}) refute the claim."
        elif verdict == Verdict.VERIFIED_TRUE:
            return f"Evidence confirms this is TRUE. {support_count} sources (including {sources_str}) support the claim."
        elif verdict == Verdict.DISPUTED:
            return f"The claim is DISPUTED. {support_count} sources support it, while {refute_count} refute it."
        elif verdict == Verdict.INSUFFICIENT_EVIDENCE:
            return "Insufficient evidence found to verify this claim."
        else:
            return "Could not verify claim with available evidence."

# Singleton instance
_synthesizer_instance = None

def get_synthesizer() -> EvidenceSynthesizer:
    global _synthesizer_instance
    if _synthesizer_instance is None:
        _synthesizer_instance = EvidenceSynthesizer()
    return _synthesizer_instance
