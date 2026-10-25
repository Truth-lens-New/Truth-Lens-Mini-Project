"""
TruthLens LLM Verdict Service

Uses Gemini to assess claims when traditional fact-checking yields insufficient evidence.
This is a fallback for obvious claims that can be verified with common knowledge.
"""

from google import genai
from app.core.config import settings


async def llm_assess_claim(claim: str) -> dict:
    """
    Use LLM to assess a claim's veracity.
    
    This is used as a FALLBACK when:
    - No fact-checks are found
    - News evidence is insufficient
    
    Args:
        claim: The claim to assess
        
    Returns:
        Dict with verdict, confidence, and reasoning
    """
    if not claim or not claim.strip():
        return {
            'verdict': None,
            'confidence': None,
            'reasoning': None,
            'used': False
        }
    
    if not settings.gemini_api_key:
        return {
            'verdict': None,
            'confidence': None,
            'reasoning': 'LLM not configured',
            'used': False
        }
    
    try:
        client = genai.Client(api_key=settings.gemini_api_key)

        
        prompt = f"""You are a fact-checker AI. Assess the following claim based on scientific consensus and widely verified facts.

CLAIM: "{claim}"

Instructions:
1. For well-known FALSE claims (flat earth, vaccine microchips, 5G conspiracies, etc.) - say FALSE with HIGH confidence.
2. For well-known TRUE claims backed by scientific consensus (climate change, vaccine safety, etc.) - say TRUE with HIGH confidence.
3. ONLY say UNCERTAIN if the claim is genuinely ambiguous or requires very recent/specialized information.
4. Be DECISIVE - most common misinformation claims have clear answers.

Respond in this EXACT format:
VERDICT: [TRUE/FALSE/UNCERTAIN]
CONFIDENCE: [HIGH/MEDIUM/LOW]
REASONING: [1-2 sentence explanation with specific facts]

Examples:
- "Earth is flat" → VERDICT: FALSE, CONFIDENCE: HIGH (Well-documented scientific fact since ancient times)
- "Vaccines cause autism" → VERDICT: FALSE, CONFIDENCE: HIGH (Debunked by extensive research, original study retracted)
- "Climate change is real" → VERDICT: TRUE, CONFIDENCE: HIGH (97% scientific consensus)

Now assess the claim:"""

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt
        )
        response_text = response.text.strip()
        
        # Parse response
        verdict = None
        confidence = None
        reasoning = None
        
        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith('VERDICT:'):
                verdict_text = line.replace('VERDICT:', '').strip().upper()
                if 'TRUE' in verdict_text and 'FALSE' not in verdict_text:
                    verdict = 'Likely True'
                elif 'FALSE' in verdict_text:
                    verdict = 'Likely False'
                elif 'UNCERTAIN' in verdict_text:
                    verdict = None  # Don't override, let default logic handle
            elif line.startswith('CONFIDENCE:'):
                conf_text = line.replace('CONFIDENCE:', '').strip().upper()
                if 'HIGH' in conf_text:
                    confidence = 'high'
                elif 'MEDIUM' in conf_text:
                    confidence = 'medium'
                else:
                    confidence = 'low'
            elif line.startswith('REASONING:'):
                reasoning = line.replace('REASONING:', '').strip()
        
        return {
            'verdict': verdict,
            'confidence': confidence,
            'reasoning': reasoning,
            'used': verdict is not None
        }
        
    except Exception as e:
        print(f"LLM claim assessment error: {e}")
        return {
            'verdict': None,
            'confidence': None,
            'reasoning': str(e),
            'used': False
        }
