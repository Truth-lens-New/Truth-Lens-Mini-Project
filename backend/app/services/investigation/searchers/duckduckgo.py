"""
DuckDuckGo Search

Free web search using DuckDuckGo.
Phase 2A: Synchronous implementation - no API key required.
"""

from typing import List, Optional
from dataclasses import dataclass
from urllib.parse import urlparse

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    print("Warning: duckduckgo-search not installed. Run: pip install duckduckgo-search")


@dataclass
class SearchResult:
    """Single search result."""
    title: str
    url: str
    snippet: str
    source_domain: str


class DuckDuckGoSearcher:
    """
    Search using DuckDuckGo.
    
    No API key required.
    
    Usage:
        searcher = DuckDuckGoSearcher()
        results = searcher.search("COVID vaccine safety")
        for r in results:
            print(f"{r.title}: {r.snippet}")
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search DuckDuckGo for a query.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of SearchResult objects
        """
        if not DDGS_AVAILABLE:
            print("DuckDuckGo search unavailable - library not installed")
            return []
        
        try:
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(
                    query, 
                    max_results=max_results,
                    safesearch='moderate'
                ))
            
            results = []
            for r in raw_results:
                domain = self._extract_domain(r.get('href', ''))
                results.append(SearchResult(
                    title=r.get('title', ''),
                    url=r.get('href', ''),
                    snippet=r.get('body', ''),
                    source_domain=domain
                ))
            
            return results
            
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []
    
    def search_news(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search DuckDuckGo News.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of SearchResult objects from news sources
        """
        if not DDGS_AVAILABLE:
            return []
        
        try:
            with DDGS() as ddgs:
                raw_results = list(ddgs.news(
                    query,
                    max_results=max_results
                ))
            
            results = []
            for r in raw_results:
                domain = self._extract_domain(r.get('url', ''))
                results.append(SearchResult(
                    title=r.get('title', ''),
                    url=r.get('url', ''),
                    snippet=r.get('body', ''),
                    source_domain=domain
                ))
            
            return results
            
        except Exception as e:
            print(f"DuckDuckGo news search error: {e}")
            return []
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        if not url:
            return "unknown"
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            return domain if domain else "unknown"
        except:
            return "unknown"


# Singleton instance
_searcher_instance: Optional[DuckDuckGoSearcher] = None


def get_duckduckgo_searcher() -> DuckDuckGoSearcher:
    """Get singleton instance of DuckDuckGoSearcher."""
    global _searcher_instance
    if _searcher_instance is None:
        _searcher_instance = DuckDuckGoSearcher()
    return _searcher_instance
