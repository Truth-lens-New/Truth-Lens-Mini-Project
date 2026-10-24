"""
TruthLens Fact Check Service

Queries Google Fact Check Tools API for existing fact-checks.
"""

from typing import Optional, Dict, List
import httpx
import google.generativeai as genai

from app.core.config import settings
from app.services.evidence.ratings import normalize_rating as _shared_normalize_rating


# Google Fact Check API endpoint
FACTCHECK_API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


async def llm_interpret_rating(rating: str, summary: str, claim: str, url: str = "", source: str = "") -> str:
    """
    Use LLM to interpret an unclear fact-check rating.
    
    Args:
        rating: Original rating text from fact-checker
        summary: Fact-check summary/excerpt (may be the claim being checked, not the conclusion)
        claim: The original claim being checked
        url: URL of the fact-check article (often contains the verdict in the title)
        source: Name of the fact-checking organization
        
    Returns:
        Interpreted rating: True, False, Misleading, or Unverifiable
    """
    if not settings.gemini_api_key:
        return 'Unverifiable'
    
    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""You are a fact-check rating interpreter. Your job is to determine whether a fact-check article SUPPORTS or REFUTES the original claim.

IMPORTANT: The "summary" field often contains the CLAIM BEING FACT-CHECKED, not the fact-checker's conclusion. You must look at the URL and source to understand the actual verdict.

ORIGINAL CLAIM TO VERIFY: "{claim}"

FACT-CHECK DETAILS:
- Source: {source}
- URL: {url}
- Rating text: "{rating}"
- Summary/excerpt: "{summary}"

CRITICAL: Look at the URL carefully - fact-check URLs often contain the verdict (e.g., "says-X-is-safe" means the article SUPPORTS safety claims, "debunks-X" means it REFUTES X).

Based on ALL the context above, what is the fact-checker's verdict on the original claim "{claim}"?

Respond with ONLY ONE of these exact words:
- TRUE (if the fact-check article SUPPORTS/CONFIRMS the original claim)
- FALSE (if the fact-check article REFUTES/DEBUNKS the original claim)
- MISLEADING (if the claim is partially true but missing context)
- UNVERIFIABLE (if unclear or insufficient information)

Your response (one word only):"""

        response = await model.generate_content_async(prompt)
        result = response.text.strip().upper()
        
        # Validate response
        if result in ['TRUE', 'FALSE', 'MISLEADING', 'UNVERIFIABLE']:
            return result.capitalize() if result != 'UNVERIFIABLE' else 'Unverifiable'
        
        return 'Unverifiable'
        
    except Exception as e:
        print(f"LLM rating interpretation error: {e}")
        return 'Unverifiable'


def normalize_rating(rating: str) -> str:
    """
    Normalize a fact-check rating using the shared, tested mapping in
    `app.services.evidence.ratings` (word-boundary phrase matching, negation
    aware: "not true" -> False, "half true" -> Misleading, ...).

    Args:
        rating: Original rating text

    Returns:
        Normalized rating: True, False, Misleading, or Unverifiable
        (None when the rating cannot be confidently mapped)
    """
    return _shared_normalize_rating(rating)


async def search_factchecks(claim: str) -> Dict:
    """
    Search for existing fact-checks for a claim.
    
    Args:
        claim: The claim to search for
        
    Returns:
        Dict with found (bool), rating, summary, source, and url
    """
    if not claim:
        return {
            'found': False,
            'rating': None,
            'summary': None,
            'source': None,
            'url': None
        }
    
    if not settings.google_factcheck_api_key:
        return {
            'found': False,
            'rating': None,
            'summary': 'Fact-check API key not configured',
            'source': None,
            'url': None
        }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                FACTCHECK_API_URL,
                params={
                    'key': settings.google_factcheck_api_key,
                    'query': claim,
                    'languageCode': 'en'
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                return {
                    'found': False,
                    'rating': None,
                    'summary': f'API error: {response.status_code}',
                    'source': None,
                    'url': None
                }
            
            data = response.json()
            claims = data.get('claims', [])
            
            if not claims:
                return {
                    'found': False,
                    'rating': None,
                    'summary': None,
                    'source': None,
                    'url': None
                }
            
            # Get the first (most relevant) claim review
            first_claim = claims[0]
            claim_reviews = first_claim.get('claimReview', [])
            
            if not claim_reviews:
                return {
                    'found': False,
                    'rating': None,
                    'summary': None,
                    'source': None,
                    'url': None
                }
            
            review = claim_reviews[0]
            original_rating = review.get('textualRating', '')
            summary_text = first_claim.get('text', '')
            article_url = review.get('url', '')
            source_name = review.get('publisher', {}).get('name', 'Unknown')
            
            # Try static normalization first
            normalized_rating = normalize_rating(original_rating)
            
            # If static mapping failed, use LLM to interpret with full context
            if normalized_rating is None:
                normalized_rating = await llm_interpret_rating(
                    rating=original_rating,
                    summary=summary_text,
                    claim=claim,
                    url=article_url,
                    source=source_name
                )
            
            return {
                'found': True,
                'rating': normalized_rating,
                'original_rating': original_rating,
                'summary': summary_text,
                'source': source_name,
                'url': article_url
            }
            
    except Exception as e:
        print(f"Fact-check API error: {e}")
        return {
            'found': False,
            'rating': None,
            'summary': f'Error: {str(e)}',
            'source': None,
            'url': None
        }
