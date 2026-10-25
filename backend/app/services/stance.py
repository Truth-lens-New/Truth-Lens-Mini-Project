"""
TruthLens Stance Classification Service

Uses Gemini to classify the stance of evidence snippets toward a claim.
"""

from typing import List, Dict
from google import genai

from app.core.config import settings
from app.services.domain_trust import score_domain


# Stance labels
STANCE_LABELS = ['SUPPORTS', 'REFUTES', 'DISCUSS', 'UNRELATED']


async def classify_stance(claim: str, snippet: str) -> str:
    """
    Classify the stance of a snippet toward a claim.
    
    Args:
        claim: The claim being verified
        snippet: Text snippet (title + description from news)
        
    Returns:
        Stance label: SUPPORTS, REFUTES, DISCUSS, or UNRELATED
    """
    if not claim or not snippet:
        return 'UNRELATED'
    
    if not settings.gemini_api_key:
        # Fallback: simple keyword matching
        snippet_lower = snippet.lower()
        claim_lower = claim.lower()
        
        # Basic keyword overlap check
        claim_words = set(claim_lower.split())
        snippet_words = set(snippet_lower.split())
        
        overlap = len(claim_words & snippet_words)
        if overlap >= 3:
            return 'DISCUSS'
        return 'UNRELATED'
    
    try:
        client = genai.Client(api_key=settings.gemini_api_key)

        
        prompt = f"""Classify the stance of the following text snippet toward the given claim.

Claim: {claim}

Snippet: {snippet}

Classify as exactly one of:
- SUPPORTS: The snippet provides evidence supporting the claim
- REFUTES: The snippet contradicts or disproves the claim
- DISCUSS: The snippet discusses the claim's topic but doesn't clearly support or refute
- UNRELATED: The snippet is not relevant to the claim

Respond with ONLY the classification label (SUPPORTS, REFUTES, DISCUSS, or UNRELATED):"""

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt
        )
        stance = response.text.strip().upper()
        
        # Validate response
        if stance in STANCE_LABELS:
            return stance
        
        # Try to extract label from response
        for label in STANCE_LABELS:
            if label in stance:
                return label
        
        return 'UNRELATED'
        
    except Exception as e:
        print(f"Stance classification error: {e}")
        return 'UNRELATED'


async def classify_all_stances(claim: str, articles: List[Dict]) -> List[Dict]:
    """
    Classify stances for all articles.
    
    Args:
        claim: The claim being verified
        articles: List of article dicts from news search
        
    Returns:
        List of articles with stance added
    """
    results = []
    
    for article in articles:
        snippet = f"{article.get('title', '')} {article.get('description', '')}"
        stance = await classify_stance(claim, snippet)
        
        results.append({
            **article,
            'stance': stance
        })
    
    return results


def weighted_stance(stances_with_domains: List[Dict]) -> Dict:
    """
    Calculate weighted stance summary based on domain trust.
    
    Args:
        stances_with_domains: List of articles with stance and domain info
        
    Returns:
        Dict with counts and weighted signals
    """
    # Trust level weights
    trust_weights = {
        'trusted': 1.0,
        'mixed': 0.5,
        'low': 0.1,
        'unknown': 0.3
    }
    
    counts = {
        'SUPPORTS': 0,
        'REFUTES': 0,
        'DISCUSS': 0,
        'UNRELATED': 0
    }
    
    weighted_scores = {
        'supports': 0.0,
        'refutes': 0.0
    }
    
    for item in stances_with_domains:
        stance = item.get('stance', 'UNRELATED')
        domain = item.get('domain')
        
        counts[stance] = counts.get(stance, 0) + 1
        
        # Get domain trust
        domain_trust = score_domain(item.get('url', ''))
        weight = trust_weights.get(domain_trust['score'], 0.3)
        
        if stance == 'SUPPORTS':
            weighted_scores['supports'] += weight
        elif stance == 'REFUTES':
            weighted_scores['refutes'] += weight
    
    return {
        'counts': counts,
        'weighted': weighted_scores,
        'total_articles': len(stances_with_domains)
    }
