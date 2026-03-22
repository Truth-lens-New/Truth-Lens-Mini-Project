
import httpx
from typing import List, Optional
from app.core.config import settings

class GoogleFactCheck:
    """
    Search Google Fact Check Tools API.
    
    API Docs: https://developers.google.com/fact-check/tools/api/reference/rest/v1alpha1/claims/search
    """
    
    API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key  # Try to reuse Gemini key if Google Cloud project has both enabled
        
    async def search(self, query: str) -> List[dict]:
        """Search for fact checks matching the query."""
        if not self.api_key:
            return []
            
        params = {
            "query": query,
            "key": self.api_key
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.API_URL, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("claims", [])
        except Exception as e:
            print(f"Google Fact Check API error: {e}")
            
        return []

# Singleton / Getter logic
_instance = None

def get_google_factcheck():
    global _instance
    if _instance is None:
        _instance = GoogleFactCheck()
    return _instance
