"""
TruthLens Evidence Services

Phase 2A: Evidence gathering and verification.
"""

from .source_trust import SourceTrustScorer, get_trust_scorer
from .wikidata_verifier import WikidataVerifier, get_wikidata_verifier
from .known_misinfo_checker import KnownMisinfoChecker, get_misinfo_checker

__all__ = [
    "SourceTrustScorer",
    "get_trust_scorer",
    "WikidataVerifier", 
    "get_wikidata_verifier",
    "KnownMisinfoChecker",
    "get_misinfo_checker",
]
