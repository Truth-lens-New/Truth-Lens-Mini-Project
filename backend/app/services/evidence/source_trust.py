"""
Source Trust Scoring

Provides trust scores for domains based on historical reliability.
Phase 2A: Synchronous, simple implementation.
"""

import json
from pathlib import Path
from urllib.parse import urlparse
from typing import Tuple, Optional


class SourceTrustScorer:
    """
    Score sources by their trustworthiness.
    
    Scores:
    - 90-100: Highly trusted (fact-checkers, major wire services, academic)
    - 70-89: Generally trusted (major newspapers)
    - 50-69: Mixed reliability (partisan sources)
    - 30-49: Low trust (tabloids, opinion sites)
    - 0-29: Very low trust (known misinformation sources)
    
    Usage:
        scorer = SourceTrustScorer()
        score, category = scorer.get_trust_score("https://reuters.com/article/...")
        # Returns: (95, "highly_trusted")
    """
    
    def __init__(self, trust_file: Optional[str] = None):
        """
        Initialize with trust scores database.
        
        Args:
            trust_file: Path to JSON file with trust scores.
                       If None, uses default location.
        """
        if trust_file is None:
            # Try multiple possible locations
            possible_paths = [
                Path("app/data/domain_trust_scores.json"),
                Path("backend/app/data/domain_trust_scores.json"),
                Path(__file__).parent.parent.parent / "data" / "domain_trust_scores.json"
            ]
            for path in possible_paths:
                if path.exists():
                    trust_file = str(path)
                    break
        
        self.trust_scores = self._load_trust_scores(trust_file) if trust_file else {}
        self.default_score = 50
    
    def _load_trust_scores(self, filepath: str) -> dict:
        """Load and flatten trust scores from JSON file."""
        path = Path(filepath)
        if not path.exists():
            print(f"Warning: Trust scores file not found: {filepath}")
            return {}
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                
            # Flatten nested structure into single dict
            flat = {}
            for category, domains in data.items():
                if isinstance(domains, dict):
                    flat.update(domains)
                elif category == "default":
                    self.default_score = domains
            return flat
            
        except json.JSONDecodeError as e:
            print(f"Error parsing trust scores JSON: {e}")
            return {}
    
    def get_trust_score(self, url_or_domain: str) -> Tuple[int, str]:
        """
        Get trust score for a URL or domain.
        
        Args:
            url_or_domain: Full URL or just domain name
            
        Returns:
            Tuple of (score, category_name)
            
        Example:
            >>> scorer.get_trust_score("https://www.reuters.com/article/...")
            (95, "highly_trusted")
        """
        domain = self._extract_domain(url_or_domain)
        
        # Try exact match first
        if domain in self.trust_scores:
            score = self.trust_scores[domain]
            return score, self._categorize(score)
        
        # Try without www prefix
        domain_no_www = domain.replace("www.", "")
        if domain_no_www in self.trust_scores:
            score = self.trust_scores[domain_no_www]
            return score, self._categorize(score)
        
        # Try parent domains (for subdomains)
        parts = domain_no_www.split(".")
        for i in range(len(parts) - 1):
            parent = ".".join(parts[i:])
            if parent in self.trust_scores:
                score = self.trust_scores[parent]
                return score, self._categorize(score)
        
        return self.default_score, "unknown"
    
    def _extract_domain(self, url_or_domain: str) -> str:
        """Extract domain from URL or return as-is if already domain."""
        if url_or_domain.startswith(("http://", "https://")):
            parsed = urlparse(url_or_domain)
            return parsed.netloc.lower()
        return url_or_domain.lower()
    
    def _categorize(self, score: int) -> str:
        """Categorize trust score into human-readable category."""
        if score >= 90:
            return "highly_trusted"
        elif score >= 70:
            return "generally_trusted"
        elif score >= 50:
            return "mixed_reliability"
        elif score >= 30:
            return "low_trust"
        else:
            return "very_low_trust"
    
    def is_fact_checker(self, url_or_domain: str) -> bool:
        """
        Check if domain is a known fact-checking organization.
        
        These get special treatment in evidence synthesis.
        """
        fact_checkers = {
            "snopes.com", "factcheck.org", "politifact.com",
            "altnews.in", "boomlive.in", "vishvasnews.com",
            "thequint.com"
        }
        domain = self._extract_domain(url_or_domain).replace("www.", "")
        return domain in fact_checkers
    
    def is_academic(self, url_or_domain: str) -> bool:
        """Check if domain is an academic/scientific source."""
        academic_domains = {
            "pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov",
            "nature.com", "science.org", "thelancet.com",
            "nejm.org", "arxiv.org", "scholar.google.com"
        }
        domain = self._extract_domain(url_or_domain).replace("www.", "")
        return domain in academic_domains or ".edu" in domain
    
    def is_government(self, url_or_domain: str) -> bool:
        """Check if domain is a government source."""
        domain = self._extract_domain(url_or_domain)
        return ".gov" in domain or domain.endswith(".gov.in")


# Singleton instance for reuse
_scorer_instance: Optional[SourceTrustScorer] = None


def get_trust_scorer() -> SourceTrustScorer:
    """Get singleton instance of SourceTrustScorer."""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = SourceTrustScorer()
    return _scorer_instance
