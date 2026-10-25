"""
TruthLens Investigation Searchers

Phase 2A: Free search engines for evidence gathering.
"""

from .duckduckgo import DuckDuckGoSearcher, get_duckduckgo_searcher
from .firecrawl import FirecrawlSearcher, get_firecrawl_searcher
from .wikipedia import WikipediaSearcher, get_wikipedia_searcher

__all__ = [
    "DuckDuckGoSearcher",
    "get_duckduckgo_searcher",
    "FirecrawlSearcher",
    "get_firecrawl_searcher",
    "get_web_searcher",
    "WikipediaSearcher",
    "get_wikipedia_searcher",
]


def get_web_searcher():
    """Prefer configured Firecrawl; otherwise preserve the existing DDG path."""
    firecrawl = get_firecrawl_searcher()
    return firecrawl if firecrawl.is_configured else get_duckduckgo_searcher()
