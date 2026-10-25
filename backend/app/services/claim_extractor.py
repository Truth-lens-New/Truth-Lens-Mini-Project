"""
TruthLens Claim Extractor Service

Extracts factual claims from text using spaCy and Gemini.
"""

from typing import List, Optional
import spacy
from google import genai

from app.core.config import settings


# Load spaCy model (lazy loading)
_nlp = None


def get_nlp():
    """Get or load spaCy NLP model."""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm", exclude=["tokenizer"])
        except OSError:
            # Model not installed, download it
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            _nlp = spacy.load("en_core_web_sm", exclude=["tokenizer"])
    return _nlp


def extract_candidates(text: str) -> List[str]:
    """
    Extract candidate sentences from text using spaCy.
    
    Args:
        text: Input text to process
        
    Returns:
        List of candidate sentences
    """
    if not text or not text.strip():
        return []
    
    nlp = get_nlp()
    doc = nlp(text)
    
    candidates = []
    for sent in doc.sents:
        sentence = sent.text.strip()
        # Filter out very short sentences or questions
        if len(sentence) > 20 and not sentence.endswith('?'):
            candidates.append(sentence)
    
    return candidates


async def refine_claims(candidates: List[str]) -> List[str]:
    """
    Use Gemini to refine candidate sentences into factual claims.
    
    Args:
        candidates: List of candidate sentences
        
    Returns:
        List of 1-3 refined factual claims
    """
    if not candidates:
        return []
    
    if not settings.gemini_api_key:
        # Fallback: return top candidates as-is
        return candidates[:3]
    
    try:
        client = genai.Client(api_key=settings.gemini_api_key)

        
        prompt = f"""Analyze the following text segments and extract 1-3 specific, verifiable factual claims.

Text segments:
{chr(10).join(f"- {c}" for c in candidates[:10])}

Rules:
1. Extract only factual claims that can be verified as true or false
2. Rephrase claims to be clear and specific
3. Do not add information not present in the original text
4. Return only the claims, one per line
5. If no verifiable claims exist, return "NO_CLAIMS"

Factual claims:"""

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt
        )
        response_text = response.text.strip()
        
        if response_text == "NO_CLAIMS":
            return []
        
        # Parse response into individual claims
        claims = [
            line.strip().lstrip('- ').lstrip('• ').lstrip('1234567890.)')
            for line in response_text.split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]
        
        return claims[:3]
        
    except Exception as e:
        print(f"Gemini claim extraction error: {e}")
        # Fallback: return top candidates
        return candidates[:3]


def get_primary_claim(claims: List[str]) -> Optional[str]:
    """
    Select the primary (most verifiable) claim.
    
    Args:
        claims: List of extracted claims
        
    Returns:
        The primary claim or None
    """
    if not claims:
        return None
    
    # Simple heuristic: return the first claim (usually most important)
    # In a more sophisticated system, this could use additional scoring
    return claims[0]


async def extract_claims(text: str) -> dict:
    """
    Full claim extraction pipeline.
    
    Args:
        text: Input text
        
    Returns:
        Dict with candidates, refined claims, and primary claim
    """
    candidates = extract_candidates(text)
    refined = await refine_claims(candidates)
    primary = get_primary_claim(refined)
    
    return {
        'candidates': candidates,
        'refined_claims': refined,
        'primary_claim': primary
    }
