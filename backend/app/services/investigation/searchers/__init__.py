"""
TruthLens Investigation Searchers

Phase 2A: Free search engines for evidence gathering.
"""

from .duckduckgo import DuckDuckGoSearcher, get_duckduckgo_searcher
from .wikipedia import WikipediaSearcher, get_wikipedia_searcher

__all__ = [
    "DuckDuckGoSearcher",
    "get_duckduckgo_searcher",
    "WikipediaSearcher",
    "get_wikipedia_searcher",
]
