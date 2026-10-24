"""
Stance Detection Service.

Uses RoBERTa-large-mnli to determine if a piece of evidence
SUPPORTS, REFUTES, or is NEUTRAL towards a claim.
"""

import re

from app.services.models.model_manager import get_model_manager

class StanceDetector:
    """
    AI-powered Stance Detection
    """
    
    DEBUNK_KEYWORDS = {
        "myth", "hoax", "fake", "misconception", "fanciful", "false belief", 
        "debunk", "refuted", "disproven", "fantasy", "legend", "urban legend",
        "conspiracy theory", "incorrectly", "erroneously"
    }

    def __init__(self):
        self.manager = get_model_manager()

    # --- Heuristic Guardrail #2 helpers: comparative entity swap ---
    # Extracts the subject of "X is/are the larger/taller/..." assertions.
    # Pronoun subjects are skipped (they can't be compared across texts).
    _COMPARATIVE_RE = re.compile(
        r"\b([A-Za-z]+)\s+(?:is|are|was|were)\s+(?:the\s+)?"
        r"(?:larger|largest|bigger|biggest|smaller|smallest|taller|tallest|shorter|shortest|"
        r"older|oldest|newer|newest|faster|fastest|slower|slowest|heavier|heaviest|lighter|lightest|"
        r"closer|closest|nearer|nearest|farther|farthest|further|furthest|brighter|brightest|"
        r"stronger|strongest|longer|longest|deeper|deepest|hotter|hottest|colder|coldest)\b",
        re.IGNORECASE,
    )
    _PRONOUN_SUBJECTS = {
        "it", "this", "that", "these", "those", "which", "there", "one",
        "they", "he", "she", "we", "you", "who", "what",
    }

    @classmethod
    def _comparative_entities(cls, text: str) -> set:
        """Return lowercased subjects of comparative assertions in `text`."""
        subjects = set()
        for match in cls._COMPARATIVE_RE.finditer(text):
            subject = match.group(1).lower()
            if subject not in cls._PRONOUN_SUBJECTS:
                subjects.add(subject)
        return subjects

    @classmethod
    def _comparative_swap(cls, claim_text: str, evidence_text: str) -> bool:
        """
        True when claim and evidence attribute the same comparative/superlative
        to different entities, e.g. claim "Deimos is the larger one" vs evidence
        "Phobos is the larger of Mars' two moons". Only one entity can hold a
        superlative, so disjoint subjects imply a contradiction.
        """
        claim_subjects = cls._comparative_entities(claim_text)
        evidence_subjects = cls._comparative_entities(evidence_text)
        if not claim_subjects or not evidence_subjects:
            return False
        return not (claim_subjects & evidence_subjects)


    async def detect_async(self, claim_text: str, evidence_text: str) -> dict:
        """
        Async wrapper for detect() to avoid blocking the event loop.
        """
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(self.detect, claim_text, evidence_text)

    def detect(self, claim_text: str, evidence_text: str) -> dict:

        """
        Detect stance of evidence towards claim using BART-Large-MNLI (Zero-Shot).
        
        Now includes 'Discussing' label and Heuristic Guardrails for myths.
        """
        # Get model (Unified BART-Large-MNLI)
        classifier = self.manager.unified_model
        
        clean_claim = claim_text.strip()
        lower_evidence = evidence_text.lower()
        
        # --- Heuristic Guardrail: Debunk Detection ---
        # If evidence mentions "myth", "hoax", etc., we should be very skeptical of "Support"
        has_debunk_term = any(term in lower_evidence for term in self.DEBUNK_KEYWORDS)
        
        # Construct dynamic labels/hypotheses
        label_support = "true"
        label_refute = "false"
        label_neutral = "unrelated"
        label_discuss = "discussing the myth" 
        
        candidate_labels = [label_support, label_refute, label_neutral, label_discuss]
        
        # Refined Template: Separates the text's content from the claim's truth value
        # "Based on this text, the claim 'X' is {true/false/unrelated/discussing}."
        template = f"Based on this text, the claim '{clean_claim}' is {{}}."
        
        try:
            result = classifier(
                evidence_text, 
                candidate_labels, 
                hypothesis_template=template,
                multi_label=False
            )
            
            # Map back to simple keys
            scores = {label: score for label, score in zip(result['labels'], result['scores'])}
            
            support_score = scores.get(label_support, 0.0)
            refute_score = scores.get(label_refute, 0.0)
            neutral_score = scores.get(label_neutral, 0.0)
            discuss_score = scores.get(label_discuss, 0.0)
            
            # --- Apply Guardrail Penalties ---
            if has_debunk_term:
                # If it's a debunking article, 'Support' effectively means 'Refutes' 
                # or it's just discussing the myth.
                # We massively penalize support and boost refute/discuss
                print(f"  [Guardrail] Debunk term detected. Penalizing Support.")
                refute_score += support_score * 0.8  # Shift support to refute
                discuss_score += support_score * 0.2
                support_score *= 0.0  # Nuke support

            # --- Heuristic Guardrail #2: Comparative entity swap ---
            # Claim asserts "X is the larger/taller/..." while evidence attributes
            # the same superlative to a different entity Y -> contradiction.
            # (Zero-shot NLI models are weak on these entity swaps.)
            if self._comparative_swap(clean_claim, evidence_text):
                print(f"  [Guardrail] Comparative entity mismatch. Penalizing Support.")
                refute_score += support_score * 0.8  # Shift support to refute
                discuss_score += support_score * 0.2
                support_score *= 0.0  # Nuke support
            
            # Re-normalize isn't strictly necessary for comparison, but clean for output
            total = support_score + refute_score + neutral_score + discuss_score + 1e-9
            support_score /= total
            refute_score /= total
            neutral_score /= total
            discuss_score /= total
            
            # Determine Verdict
            THRESHOLD = 0.40
            
            if support_score > THRESHOLD and support_score > refute_score and support_score > neutral_score and support_score > discuss_score:
                label = "SUPPORTS"
                final_score = support_score
            elif refute_score > THRESHOLD and refute_score > support_score:
                label = "REFUTES"
                final_score = refute_score
            elif discuss_score > THRESHOLD and discuss_score > support_score:
                # discussing a myth without calling it true -> likely Refutes or Neutral context
                # For safety, map 'Discussing' to NEUTRAL in the strict sense, 
                # OR REFUTES if we are strict. Let's map to NEUTRAL-leaning-Refute.
                # Actually, if it's "discussing a myth", it's effectively Neutral/Refutes.
                label = "NEUTRAL" 
                final_score = discuss_score
            else:
                label = "NEUTRAL"
                final_score = neutral_score
                
            return {
                "label": label,
                "score": final_score,
                "raw_scores": {
                    "support": support_score,
                    "refute": refute_score,
                    "neutral": neutral_score,
                    "discuss": discuss_score
                }
            }
            
        except Exception as e:
            print(f"Stance detection error: {e}")
            return {
                "label": "NEUTRAL",
                "score": 0.0,
                "raw_scores": {"support": 0, "refute": 0, "neutral": 0}
            }
