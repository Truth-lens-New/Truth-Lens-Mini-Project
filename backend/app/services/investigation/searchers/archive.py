"""
Archive.org Searcher

Module for searching historical web data via Wayback Machine API.
"""

import httpx
import logging
from typing import List, Optional
from app.services.investigation.searchers.duckduckgo import SearchResult

logger = logging.getLogger(__name__)

class ArchiveOrgSearcher:
    """
    Search Wayback Machine for historical snapshots.
    """
    
    BASE_URL = "http://archive.org/wayback/available"
    
    async def search(self, url: str) -> List[SearchResult]:
        """
        Check if a URL has an archived snapshot.
        """
        results = []
        try:
            async with httpx.AsyncClient() as client:
                params = {"url": url}
                resp = await client.get(self.BASE_URL, params=params, timeout=10.0)
                
                if resp.status_code == 200:
                    data = resp.json()
                    snapshots = data.get("archived_snapshots", {})
                    closest = snapshots.get("closest", {})
                    
                    if closest and closest.get("available"):
                        results.append(SearchResult(
                            title=f"Archived Snapshot ({closest.get('timestamp')})",
                            url=closest.get("url"),
                            snippet=f"Archived version of {url} from {closest.get('timestamp')}",
                            source="Wayback Machine",
                            source_domain="web.archive.org"
                        ))
                        
        except Exception as e:
            logger.error(f"Archive.org search error: {e}")
            
        return results
