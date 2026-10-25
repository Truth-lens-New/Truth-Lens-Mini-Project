"""
TruthLens News Search Service

Retrieves related news articles using GNews API.
"""

from typing import List, Dict
import httpx

from app.core.config import settings
from app.services.domain_trust import extract_domain
from app.services.investigation.searchers import get_web_searcher


# GNews API endpoint
GNEWS_API_URL = "https://gnews.io/api/v4/search"


async def search_news(claim: str, max_results: int = 5) -> List[Dict]:
    """
    Search for news articles related to a claim.
    
    Args:
        claim: The claim to search for
        max_results: Maximum number of results to return
        
    Returns:
        List of article dicts with title, description, domain, url
    """
    if not claim:
        return []
    
    if not settings.gnews_api_key:
        return await _search_with_web_provider(claim, max_results)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GNEWS_API_URL,
                params={
                    'apikey': settings.gnews_api_key,
                    'q': claim[:200],  # Limit query length
                    'lang': 'en',
                    'max': max_results,
                    'sortby': 'relevance'
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            articles = data.get('articles', [])
            
            results = []
            for article in articles:
                url = article.get('url', '')
                results.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'domain': extract_domain(url),
                    'url': url,
                    'source': article.get('source', {}).get('name', ''),
                    'published_at': article.get('publishedAt', '')
                })
            
            return results
            
    except Exception as e:
        print(f"GNews API error: {e}")
        return await _search_with_web_provider(claim, max_results)


async def _search_with_web_provider(claim: str, max_results: int) -> List[Dict]:
    """Use Firecrawl (when configured) or DDG as the GNews fallback."""
    results = await get_web_searcher().search(f"{claim} news", max_results=max_results)
    return [
        {
            'title': result.title,
            'description': result.snippet,
            'domain': result.source_domain,
            'url': result.url,
            'source': result.source,
            'published_at': ''
        }
        for result in results
    ]
