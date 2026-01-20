"""
Stance Detection Service.

Uses RoBERTa-large-mnli to determine if a piece of evidence
SUPPORTS, REFUTES, or is NEUTRAL towards a claim.
"""

from app.services.models.model_manager import get_model_manager

class StanceDetector:
    """
    AI-powered Stance Detection
    """
    
    def __init__(self):
        self.manager = get_model_manager()
        
    def detect(self, claim_text: str, evidence_text: str) -> dict:
        """
        Detect stance of evidence towards claim using BART-Large-MNLI (Zero-Shot).
        
        We construct 3 hypotheses and check which one the evidence entails:
        1. Support: "The evidence supports the claim that {claim}"
        2. Refute: "The evidence contradicts the claim that {claim}"
        3. Neutral: "The evidence is unrelated to the claim that {claim}"
        """
        # Get model (Unified BART-Large-MNLI)
        classifier = self.manager.unified_model
        
        # Construct dynamic labels/hypotheses
        # We strip the claim to ensure it fits and doesn't have weird trailing chars
        clean_claim = claim_text.strip()
        
        # Labels are effectively the full hypotheses we want to test
        label_support = f"supports the claim that {clean_claim}"
        label_refute = f"contradicts the claim that {clean_claim}"
        label_neutral = f"is unrelated to the claim {clean_claim}"
        
        candidate_labels = [label_support, label_refute, label_neutral]
        
        # Use a template that frames the evidence's relation to the claim
        # Template: "This text {}." -> "This text supports the claim that X."
        try:
            result = classifier(
                evidence_text, 
                candidate_labels, 
                hypothesis_template="This text {}.",
                multi_label=False
            )
            
            # Map back to simple keys
            scores = {label: score for label, score in zip(result['labels'], result['scores'])}
            
            support_score = scores.get(label_support, 0.0)
            refute_score = scores.get(label_refute, 0.0)
            neutral_score = scores.get(label_neutral, 0.0)
            
            # Determine Verdict
            # We use a restrictive threshold to avoid noise
            THRESHOLD = 0.55
            
            if support_score > refute_score and support_score > neutral_score and support_score > THRESHOLD:
                label = "SUPPORTS"
                final_score = support_score
            elif refute_score > support_score and refute_score > neutral_score and refute_score > THRESHOLD:
                label = "REFUTES"
                final_score = refute_score
            else:
                label = "NEUTRAL"
                final_score = neutral_score
                
            return {
                "label": label,
                "score": final_score,
                "raw_scores": {
                    "support": support_score,
                    "refute": refute_score,
                    "neutral": neutral_score
                }
            }
            
        except Exception as e:
            print(f"Stance detection error: {e}")
            return {
                "label": "NEUTRAL",
                "score": 0.0,
                "raw_scores": {"support": 0, "refute": 0, "neutral": 0}
            }
