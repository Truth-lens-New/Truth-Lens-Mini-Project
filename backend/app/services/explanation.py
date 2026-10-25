"""
TruthLens Explanation Service

Generates user-friendly explanations using Gemini based on analysis signals.
"""

from typing import Dict
from google import genai

from app.core.config import settings


async def generate_explanation(signals: Dict) -> str:
    """
    Generate a user-friendly explanation from analysis signals.
    
    Args:
        signals: Dict containing:
            - claim: The primary claim
            - verdict: Final verdict
            - confidence: Confidence level
            - factcheck: Fact-check result
            - stance_summary: Evidence stance summary
            - domain_trust: Domain trust info
            
    Returns:
        Human-readable explanation string
    """
    claim = signals.get('claim', 'Unknown claim')
    verdict = signals.get('verdict', 'Unknown')
    confidence = signals.get('confidence', 'low')
    factcheck = signals.get('factcheck', {})
    stance_summary = signals.get('stance_summary', {})
    domain_trust = signals.get('domain_trust', {})
    
    if not settings.gemini_api_key:
        # Fallback: generate simple template-based explanation
        return _generate_fallback_explanation(signals)
    
    try:
        client = genai.Client(api_key=settings.gemini_api_key)

        
        # Build context for the LLM
        context_parts = [
            f"Claim analyzed: \"{claim}\"",
            f"Final verdict: {verdict}",
            f"Confidence level: {confidence}",
        ]
        
        if factcheck.get('found'):
            context_parts.append(
                f"Fact-check found: {factcheck.get('rating')} "
                f"(Source: {factcheck.get('source', 'Unknown')})"
            )
        else:
            context_parts.append("No existing fact-check found for this claim.")
        
        counts = stance_summary.get('counts', {})
        if any(counts.values()):
            context_parts.append(
                f"Evidence analysis: {counts.get('SUPPORTS', 0)} sources support, "
                f"{counts.get('REFUTES', 0)} sources refute, "
                f"{counts.get('DISCUSS', 0)} sources discuss the claim."
            )
        
        if domain_trust.get('domain'):
            context_parts.append(
                f"Source domain ({domain_trust['domain']}): "
                f"Trust level is {domain_trust.get('score', 'unknown')}."
            )
        
        context = "\n".join(context_parts)
        
        prompt = f"""Based on the following analysis signals, write a brief, user-friendly explanation (2-3 sentences) of why the claim received this verdict.

{context}

Rules:
1. Use only the information provided above - do not add external information
2. Be clear and accessible to a general audience
3. Explain the key factors that led to this verdict
4. Do not use technical jargon

Explanation:"""

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt
        )
        return response.text.strip()
        
    except Exception as e:
        print(f"Explanation generation error: {e}")
        return _generate_fallback_explanation(signals)


def _generate_fallback_explanation(signals: Dict) -> str:
    """
    Generate a simple template-based explanation when LLM is unavailable.
    
    Args:
        signals: Analysis signals dict
        
    Returns:
        Template-based explanation string
    """
    verdict = signals.get('verdict', 'Unknown')
    confidence = signals.get('confidence', 'low')
    factcheck = signals.get('factcheck', {})
    
    if factcheck.get('found'):
        return (
            f"This claim has been rated as '{factcheck.get('rating')}' by "
            f"{factcheck.get('source', 'a fact-checking organization')}. "
            f"Our verdict is {verdict} with {confidence} confidence."
        )
    
    stance = signals.get('stance_summary', {}).get('counts', {})
    supports = stance.get('SUPPORTS', 0)
    refutes = stance.get('REFUTES', 0)
    
    if supports > refutes:
        evidence_desc = "supporting evidence from news sources"
    elif refutes > supports:
        evidence_desc = "contradicting evidence from news sources"
    else:
        evidence_desc = "limited or mixed evidence"
    
    return (
        f"Based on {evidence_desc}, our analysis suggests this claim is "
        f"{verdict}. Confidence level: {confidence}."
    )
