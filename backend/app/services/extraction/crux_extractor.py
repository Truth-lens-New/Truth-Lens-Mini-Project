"""
TruthLens Crux Extractor
Uses Gemini 2.5 Flash to distill long texts into core factual claims.
"""

import json
import logging
import os
from typing import List
import google.generativeai as genai
from app.models.domain import RawClaim

logger = logging.getLogger(__name__)

class CruxExtractor:
    """
    Intelligent claim extraction using LLMs.
    Extracts the 'Crux' (core arguments) rather than every sentence.
    """
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found. CruxExtractor disabled.")
            self.enabled = False
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.enabled = True

    def extract(self, text: str, max_claims: int = 7) -> List[RawClaim]:
        """
        Extract core claims from text using Gemini.
        Returns a list of RawClaim objects.
        """
        if not self.enabled:
            return []

        prompt = f"""
        You are an expert Fact-Checker and Argument Analyst.
        
        TASK:
        Analyze the following text and extract the {max_claims} most critical, specific, and verifiable factual claims.
        Focus on the "Crux" of the argument—the central pillars that, if proven false, would debunk the entire narrative.
        
        RULES:
        1. Extract strictly factual assertions (e.g., "NASA used studio lights in 1969"), not opinions.
        2. Combine redundant points into single strong claims.
        3. Ignore minor details, conversational filler, or background noise.
        4. Return ONLY a JSON list of strings. No markdown, no explanations.
        
        TEXT TO ANALYZE:
        {text[:50000]}  # Limit context window just in case
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean up potential markdown code blocks
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
                
            claim_strings = json.loads(result_text)
            
            if not isinstance(claim_strings, list):
                logger.error("Gemini returned invalid format (not a list).")
                return []
                
            # Convert to RawClaim objects
            claims = []
            for i, txt in enumerate(claim_strings):
                claims.append(RawClaim(
                    text=txt,
                    sentence_index=i,
                    char_start=0, # Approximate/Unknown for synthesis
                    char_end=len(txt),
                    is_assertion=True,
                    canonical_id=None
                ))
            
            logger.info(f"CruxExtractor found {len(claims)} core claims.")
            return claims
            
        except Exception as e:
            logger.error(f"Crux extraction failed: {e}")
            return []
