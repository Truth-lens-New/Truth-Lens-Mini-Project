"""
Claim Normalizer Service

Normalizes claims to a canonical form using semantic embeddings.
Enables deduplication and caching of investigation results.

Safety guards (added):
- An exact normalized-text match is always reused (cannot contradict itself).
- A similarity match only reuses a cached result when the polarity signature
  (negation + numbers) is IDENTICAL: "vaccines cause autism" and
  "vaccines do not cause autism" embed very closely but must never share a
  verdict, and "inflation fell to 3.1%" must not inherit the 4.1% verdict.
"""

import hashlib
import re
from datetime import datetime
from typing import Optional, Dict, List, Tuple

import numpy as np

from app.services.models.model_manager import get_model_manager

# Negation tokens used to build the polarity signature (word boundaries).
_NEGATION_RE = re.compile(
    r"\b(?:not|no|never|none|nobody|nothing|neither|nor|cannot|without|"
    r"isn'?t|wasn'?t|aren'?t|weren'?t|don'?t|doesn'?t|didn'?t|won'?t|"
    r"can'?t|couldn'?t|shouldn'?t|wouldn'?t)\b"
)


class ClaimNormalizer:
    """
    Normalizes claims using vector similarity.
    Maintains a cache of known canonical claims.
    """
    
    _instance = None
    
    # Semantic similarity threshold (0.0 to 1.0)
    # 0.80 allows for slight variations (0.83 was seen for PM example)
    SIMILARITY_THRESHOLD = 0.80
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.models = get_model_manager()
        # In-memory store for MVP: List of (embedding, data)
        # In production, this would be a Vector DB (pgvector)
        self.known_claims: List[Tuple[np.ndarray, Dict]] = []

    @staticmethod
    def polarity_signature(text: str) -> Tuple[bool, frozenset]:
        """
        Build a cheap polarity signature: (has_negation, set_of_numbers).

        Two claims with different signatures must never share a cached result,
        no matter how similar their embeddings are.
        """
        lowered = (text or "").lower()
        negated = bool(_NEGATION_RE.search(lowered))
        numbers = frozenset(re.findall(r"\d+(?:\.\d+)?", lowered or ""))
        return (negated, numbers)

    @staticmethod
    def exact_key(text: str) -> str:
        """Normalized text key for guaranteed-exact duplicate detection."""
        return re.sub(r"\s+", " ", (text or "").strip().lower())

    def normalize(self, text: str) -> Dict:
        """
        Normalize input text to canonical claim.
        Returns dict with canonical text, id (if found), and similarity score.
        """
        cutoff_polarity = self.polarity_signature(text)
        exact = self.exact_key(text)

        # 1. Get embedding for input text
        embedding = self.models.get_embedding(text)

        # 2. Search for existing claim:
        #    a) exact normalized-text match (always safe to reuse)
        #    b) semantic match, guarded by an identical polarity signature
        match = self._find_exact_match(exact)
        if match is None:
            semantic_match = self._find_best_match(embedding)
            if semantic_match is not None:
                canonical_data, score = semantic_match
                if self.polarity_signature(canonical_data["text"]) == cutoff_polarity:
                    match = semantic_match
                else:
                    # Contradictory wording (negation flips) or materially
                    # different numbers: treat as a NEW claim, never reuse.
                    match = None

        if match:
            canonical_data, score = match
            return {
                "original_text": text,
                "canonical_text": canonical_data["text"],
                "canonical_id": canonical_data["id"],
                "is_duplicate": True,
                "similarity_score": float(score),
                "cached_result": canonical_data.get("result")
            }
        
        # 3. If no match, this is a new canonical claim
        # Generate a simple ID (hash of text for MVP)
        claim_id = hashlib.md5(text.encode()).hexdigest()
        
        new_claim_data = {
            "id": claim_id,
            "text": text,
            "created_at": datetime.now(),
            "result": None,  # To be filled after investigation
            "exact_key": exact,
            "polarity": cutoff_polarity,
        }
        
        # Store it
        self.known_claims.append((embedding, new_claim_data))
        
        return {
            "original_text": text,
            "canonical_text": text,
            "canonical_id": claim_id,
            "is_duplicate": False,
            "similarity_score": 1.0,
            "cached_result": None
        }

    def update_result(self, claim_id: str, result) -> None:
        """Update result for a canonical claim."""
        for i, (emb, data) in enumerate(self.known_claims):
            if data["id"] == claim_id:
                data["result"] = result
                self.known_claims[i] = (emb, data)
                break

    def _find_exact_match(self, exact_key: str) -> Optional[Tuple[Dict, float]]:
        """Return (data, 1.0) when a stored claim matches the exact key."""
        if not exact_key:
            return None
        for _, data in self.known_claims:
            if data.get("exact_key") == exact_key:
                return data, 1.0
        return None

    def _find_best_match(self, query_embedding: np.ndarray) -> Optional[Tuple[Dict, float]]:
        """Find best matching claim with cosine similarity."""
        best_score = -1.0
        best_match = None
        
        for stored_embedding, data in self.known_claims:
            # Cosine similarity
            dot_product = np.dot(query_embedding, stored_embedding)
            norm_q = np.linalg.norm(query_embedding)
            norm_s = np.linalg.norm(stored_embedding)

            if norm_q == 0 or norm_s == 0:
                continue
            score = dot_product / (norm_q * norm_s)
            
            if score > best_score:
                best_score = score
                best_match = data
                
        if best_score >= self.SIMILARITY_THRESHOLD:
            return best_match, best_score
            
        return None

def get_normalizer() -> ClaimNormalizer:
    return ClaimNormalizer()
