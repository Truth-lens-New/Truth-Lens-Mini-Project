"""
Known Misinformation Checker

Checks claims against a database of known debunked misinformation.
Phase 2A: Fast local lookup for common false claims.
"""

import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class MisinfoMatch:
    """Result from misinformation database lookup."""
    matched: bool
    claim_id: str
    verdict: str  # "VERIFIED_FALSE"
    confidence: float
    reason: str
    sources: List[str]
    pattern_matched: str


class KnownMisinfoChecker:
    """
    Check claims against known misinformation database.
    
    This provides fast verification for commonly debunked claims
    without needing to search the internet.
    
    Usage:
        checker = KnownMisinfoChecker()
        result = checker.check("COVID vaccines cause autism")
        if result.matched:
            print(f"Known misinfo: {result.reason}")
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize with misinformation database.
        
        Args:
            db_path: Path to JSON database. If None, uses default location.
        """
        if db_path is None:
            possible_paths = [
                Path("app/data/known_misinformation.json"),
                Path("backend/app/data/known_misinformation.json"),
                Path(__file__).parent.parent.parent / "data" / "known_misinformation.json"
            ]
            for path in possible_paths:
                if path.exists():
                    db_path = str(path)
                    break
        
        self.database = self._load_database(db_path) if db_path else {}
    
    def _load_database(self, filepath: str) -> Dict[str, Any]:
        """Load misinformation database from JSON."""
        path = Path(filepath)
        if not path.exists():
            print(f"Warning: Misinformation database not found: {filepath}")
            return {}
        
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing misinformation database: {e}")
            return {}
    
    def check(self, claim_text: str) -> Optional[MisinfoMatch]:
        """
        Check if claim matches known misinformation.
        
        Args:
            claim_text: The claim to check
            
        Returns:
            MisinfoMatch if found, None otherwise
        """
        claim_lower = claim_text.lower()
        
        for claim_id, data in self.database.items():
            patterns = data.get("patterns", [])
            
            # Check if all patterns are present in the claim
            if self._matches_patterns(claim_lower, patterns):
                return MisinfoMatch(
                    matched=True,
                    claim_id=claim_id,
                    verdict=data.get("verdict", "VERIFIED_FALSE"),
                    confidence=data.get("confidence", 0.95),
                    reason=data.get("reason", "Known misinformation"),
                    sources=data.get("sources", []),
                    pattern_matched=", ".join(patterns)
                )
        
        return None
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """
        Check if text contains all required patterns.
        
        A claim matches if it contains ALL patterns in the list.
        """
        if not patterns:
            return False
        
        # Require at least 2 out of 3 patterns (for flexibility)
        matches = sum(1 for p in patterns if p.lower() in text)
        threshold = max(2, len(patterns) - 1)  # All patterns or all-1
        
        return matches >= threshold
    
    def get_all_claims(self) -> List[str]:
        """Get list of all known misinformation claim IDs."""
        return list(self.database.keys())
    
    def add_claim(self, claim_id: str, patterns: List[str], 
                  verdict: str, reason: str, sources: List[str],
                  confidence: float = 0.95):
        """
        Add a new claim to the database (in memory only).
        
        For persistent storage, save to JSON file separately.
        """
        self.database[claim_id] = {
            "patterns": patterns,
            "verdict": verdict,
            "confidence": confidence,
            "reason": reason,
            "sources": sources
        }


# Singleton instance
_checker_instance: Optional[KnownMisinfoChecker] = None


def get_misinfo_checker() -> KnownMisinfoChecker:
    """Get singleton instance of KnownMisinfoChecker."""
    global _checker_instance
    if _checker_instance is None:
        _checker_instance = KnownMisinfoChecker()
    return _checker_instance
