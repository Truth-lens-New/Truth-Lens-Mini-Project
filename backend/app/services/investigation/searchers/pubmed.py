"""
PubMed Searcher

Module for searching scientific literature via NCBI Entrez API.
Async implementation using httpx.
"""

import httpx
import logging
from typing import List, Optional
from datetime import datetime
from app.services.investigation.searchers.duckduckgo import SearchResult

logger = logging.getLogger(__name__)

class PubMedSearcher:
    """
    Search PubMed for scientific/medical claims.
    Uses NCBI E-utilities API.
    """
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, email: str = "truthlens@example.com"):
        # NCBI requires an email for API usage
        self.email = email
    
    async def search(self, query: str, max_results: int = 3) -> List[SearchResult]:
        """
        Search PubMed.
        
        Flow:
        1. ESearch: Get list of UIDs for query
        2. ESummary: Get details for those UIDs
        """
        results = []
        try:
            async with httpx.AsyncClient() as client:
                # Step 1: Search for IDs
                search_params = {
                    "db": "pubmed",
                    "term": query,
                    "retmode": "json",
                    "retmax": max_results,
                    "email": self.email
                }
                
                resp = await client.get(f"{self.BASE_URL}/esearch.fcgi", params=search_params, timeout=10.0)
                if resp.status_code != 200:
                    logger.error(f"PubMed Search failed: {resp.status_code}")
                    return results
                
                data = resp.json()
                id_list = data.get("esearchresult", {}).get("idlist", [])
                
                if not id_list:
                    return results
                
                # Step 2: Get Summary/Details
                # ESummary gives metadata, EFetch gives abstract. 
                # EFetch is better for content.
                ids_str = ",".join(id_list)
                fetch_params = {
                    "db": "pubmed",
                    "id": ids_str,
                    "retmode": "xml", # XML is standard for EFetch, JSON not always available for fetch
                    # actually use esummary for JSON support if we just want title/source
                    # but we want abstract? 
                    # Let's use ESummary for JSON simplicity first.
                }
                
                # Use esummary for now as it supports JSON
                summary_params = {
                    "db": "pubmed",
                    "id": ids_str,
                    "retmode": "json",
                     "email": self.email
                }
                
                resp = await client.get(f"{self.BASE_URL}/esummary.fcgi", params=summary_params, timeout=10.0)
                if resp.status_code != 200:
                    return results

                summary_data = resp.json()
                result_dict = summary_data.get("result", {})
                
                for uid in id_list:
                    item = result_dict.get(uid)
                    if not item: continue
                    
                    title = item.get("title", "")
                    source = item.get("source", "PubMed")
                    pubdate = item.get("pubdate", "")
                    
                    # Construct search result
                    results.append(SearchResult(
                        title=title,
                        url=f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                        snippet=f"Published in {source} ({pubdate}). Title: {title}",
                        source="PubMed",
                        source_domain="pubmed.ncbi.nlm.nih.gov"
                    ))
                    
        except Exception as e:
            logger.error(f"PubMed search error: {e}")
            
        return results
