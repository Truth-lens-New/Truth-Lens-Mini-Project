"""
Wikipedia Search

Free Wikipedia API for encyclopedia lookups.
Phase 2A: Synchronous implementation - no API key required.
"""

import httpx
from typing import List, Dict, Optional
from dataclasses import dataclass
import urllib.parse


@dataclass
class WikipediaResult:
    """Single Wikipedia result."""
    title: str
    extract: str  # Summary text
    url: str
    description: Optional[str] = None


class WikipediaSearcher:
    """
    Search and retrieve Wikipedia articles.
    
    Uses the REST API - no key required.
    
    Usage:
        searcher = WikipediaSearcher()
        results = searcher.search("COVID-19 vaccine")
        summary = searcher.get_summary("COVID-19_vaccine")
    """
    
    REST_API = "https://en.wikipedia.org/api/rest_v1"
    SEARCH_API = "https://en.wikipedia.org/w/api.php"
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def search(self, query: str, limit: int = 5) -> List[WikipediaResult]:
        """
        Search Wikipedia for articles matching query.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of WikipediaResult objects with titles and descriptions
        """
        params = {
            "action": "opensearch",
            "search": query,
            "limit": limit,
            "format": "json",
            "namespace": 0  # Main articles only
        }
        
        try:
            response = httpx.get(
                self.SEARCH_API,
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": "TruthLens/1.0 (fact-checking)"}
            )
            response.raise_for_status()
            data = response.json()
            
            # OpenSearch returns: [query, [titles], [descriptions], [urls]]
            if len(data) >= 4:
                results = []
                for i, title in enumerate(data[1]):
                    results.append(WikipediaResult(
                        title=title,
                        extract=data[2][i] if i < len(data[2]) else "",
                        url=data[3][i] if i < len(data[3]) else "",
                        description=data[2][i] if i < len(data[2]) else None
                    ))
                return results
            return []
            
        except Exception as e:
            print(f"Wikipedia search error: {e}")
            return []
    
    def get_summary(self, title: str) -> Optional[WikipediaResult]:
        """
        Get article summary by title.
        
        Args:
            title: Wikipedia article title (spaces or underscores ok)
            
        Returns:
            WikipediaResult with full extract, or None if not found
        """
        # URL-encode the title
        encoded_title = urllib.parse.quote(title.replace(" ", "_"))
        url = f"{self.REST_API}/page/summary/{encoded_title}"
        
        try:
            response = httpx.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": "TruthLens/1.0 (fact-checking)"}
            )
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            data = response.json()
            
            page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
            
            return WikipediaResult(
                title=data.get("title", title),
                extract=data.get("extract", ""),
                url=page_url,
                description=data.get("description", None)
            )
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            print(f"Wikipedia summary error: {e}")
            return None
        except Exception as e:
            print(f"Wikipedia summary error: {e}")
            return None
    
    def get_extract_for_claim(self, claim: str, max_articles: int = 3) -> List[WikipediaResult]:
        """
        Search for articles relevant to a claim and get their extracts.
        
        Combines search + get_summary for comprehensive results.
        
        Args:
            claim: The claim text to search for
            max_articles: Maximum articles to fetch summaries for
            
        Returns:
            List of WikipediaResult with full extracts
        """
        # First, search for relevant articles
        search_results = self.search(claim, limit=max_articles)
        
        # Get full summaries for top results
        results = []
        for sr in search_results:
            if sr.title:
                summary = self.get_summary(sr.title)
                if summary and summary.extract:
                    results.append(summary)
        
        return results


# Singleton instance
_searcher_instance: Optional[WikipediaSearcher] = None


def get_wikipedia_searcher() -> WikipediaSearcher:
    """Get singleton instance of WikipediaSearcher."""
    global _searcher_instance
    if _searcher_instance is None:
        _searcher_instance = WikipediaSearcher()
    return _searcher_instance
