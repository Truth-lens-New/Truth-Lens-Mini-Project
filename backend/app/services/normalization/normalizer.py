"""
Claim Normalizer Service

Normalizes claims to a canonical form using semantic embeddings.
Enables deduplication and caching of investigation results.
"""

from typing import Optional, Dict, List, Tuple
import numpy as np
from datetime import datetime

from app.services.models.model_manager import get_model_manager

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
        
    def normalize(self, text: str) -> Dict:
        """
        Normalize input text to canonical claim.
        Returns dict with canonical text, id (if found), and similarity score.
        """
        # 1. Get embedding for input text
        embedding = self.models.get_embedding(text)
        
        # 2. Search for existing similar claim
        match = self._find_best_match(embedding)
        
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
        import hashlib
        claim_id = hashlib.md5(text.encode()).hexdigest()
        
        new_claim_data = {
            "id": claim_id,
            "text": text,
            "created_at": datetime.now(),
            "result": None # To be filled after investigation
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

    def update_result(self, claim_id: str, result: Dict):
        """Update result for a canonical claim."""
        for i, (emb, data) in enumerate(self.known_claims):
            if data["id"] == claim_id:
                data["result"] = result
                self.known_claims[i] = (emb, data)
                break

    def _find_best_match(self, query_embedding: np.ndarray) -> Optional[Tuple[Dict, float]]:
        """Find best matching claim with cosine similarity."""
        best_score = -1.0
        best_match = None
        
        for stored_embedding, data in self.known_claims:
            # Cosine similarity
            dot_product = np.dot(query_embedding, stored_embedding)
            norm_q = np.linalg.norm(query_embedding)
            norm_s = np.linalg.norm(stored_embedding)
            
            score = dot_product / (norm_q * norm_s)
            
            if score > best_score:
                best_score = score
                best_match = data
                
        if best_score >= self.SIMILARITY_THRESHOLD:
            return best_match, best_score
            
        return None

def get_normalizer() -> ClaimNormalizer:
    return ClaimNormalizer()
