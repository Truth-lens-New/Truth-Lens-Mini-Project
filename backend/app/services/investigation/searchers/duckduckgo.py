"""
DuckDuckGo Search

Free web search using DuckDuckGo.
Phase 2A: Synchronous implementation - no API key required.
"""

from typing import List, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
import asyncio

from ddgs import DDGS


@dataclass
class SearchResult:
    """Single search result."""
    title: str
    url: str
    snippet: str
    source: str
    source_domain: str


class DuckDuckGoSearcher:
    """
    Search using DuckDuckGo Instant Answers API (Async).
    
    Why AsyncDDGS?
    - Non-blocking I/O
    - Parallel execution support for Phase 2B
    """
    
    def __init__(self, region: str = "in-en", safe_search: str = "moderate"):
        # NOTE: 'wt-wt' (ddgs's "no region" default) resolves to a broken
        # wt.wikipedia.org mirror and fails with DNS errors; an explicit
        # region keeps searches working.
        self.region = region
        self.safe_search = safe_search
    
    async def search(self, query: str, max_results: int = 5, time: Optional[str] = None) -> List[SearchResult]:
        """
        Perform a DuckDuckGo search (Async via threadpool).
        
        Since duckduckgo_search v8+ is synchronous, we offload to a thread
        to prevent blocking the event loop.
        
        Args:
            query: Search query
            max_results: Max number of results
            time: Time filter ('d', 'w', 'm', 'y') or None
        """
        results = []
        retries = 3
        
        for attempt in range(retries):
            try:
                # Run sync DDGS in a thread
                ddg_results = await asyncio.to_thread(
                    self._run_sync_search, query, max_results, time
                )
                
                # If we get here, it succeeded
                if not ddg_results:
                     print(f"DuckDuckGo returned 0 results for '{query}' (Attempt {attempt+1}/{retries})")
                     if attempt < retries - 1:
                         await asyncio.sleep(2)
                         continue
                     return []

                # Parse results
                for r in ddg_results:
                    from urllib.parse import urlparse
                    try:
                        domain = urlparse(r.get('href', '')).netloc.replace('www.', '')
                    except:
                        domain = "unknown"
                        
                    results.append(SearchResult(
                        title=r.get('title', ''),
                        url=r.get('href', ''),
                        snippet=r.get('body', ''),
                        source="DuckDuckGo",
                        source_domain=domain
                    ))
                
                if results:
                    return results
                
            except Exception as e:
                print(f"DuckDuckGo search error (Attempt {attempt+1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 * (attempt + 1))
                else:
                    print("DuckDuckGo search failed after all retries.")
                    return []
                    
        return results

    def _run_sync_search(self, query: str, max_results: int, time: Optional[str] = None):
        """Helper to run sync search in thread.

        Tries the configured region first, then falls back to other regions:
        DuckDuckGo's per-region backends occasionally return nothing or fail,
        and a single dead region must not zero out the whole search.
        """
        fallback_regions = [r for r in ("us-en", "de-de") if r != self.region]
        with DDGS() as ddgs:
            for region in [self.region] + fallback_regions:
                try:
                    results = ddgs.text(
                        query,
                        region=region,
                        safesearch=self.safe_search,
                        max_results=max_results,
                        timelimit=time,
                    )
                    if results:
                        return results
                except Exception as exc:
                    print(f"DuckDuckGo region '{region}' failed: {exc}")
                    continue
        return []


# Singleton instance
_searcher_instance: None | DuckDuckGoSearcher = None


def get_duckduckgo_searcher() -> DuckDuckGoSearcher:
    """Get singleton instance of DuckDuckGoSearcher."""
    global _searcher_instance
    if _searcher_instance is None:
        _searcher_instance = DuckDuckGoSearcher()
    return _searcher_instance
