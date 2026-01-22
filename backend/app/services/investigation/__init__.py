"""
TruthLens Investigation Services

Phase 2A: Evidence gathering and investigation.
"""

from .searchers import (
    DuckDuckGoSearcher, get_duckduckgo_searcher,
    WikipediaSearcher, get_wikipedia_searcher
)
from .synthesizer import EvidenceSynthesizer, get_synthesizer
from .orchestrator import InvestigationOrchestrator, get_orchestrator
from .verdict_engine import VerdictEngine, get_verdict_engine

__all__ = [
    # Searchers
    "DuckDuckGoSearcher",
    "get_duckduckgo_searcher", 
    "WikipediaSearcher",
    "get_wikipedia_searcher",
    # Core
    "EvidenceSynthesizer",
    "get_synthesizer",
    "InvestigationOrchestrator",
    "get_orchestrator",
    "VerdictEngine",
    "get_verdict_engine",
]
