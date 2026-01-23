"""
Explanation Service (Phase 4)

Responsible for generating human-readable, context-aware explanations
using the LLM (Gemini Pro), grounded in the verified evidence and
strategy-specific statistics.
"""

from typing import Dict, Any, List, Optional
from app.models.evidence import VerifiedClaim, EvidenceItem, Verdict
from app.models.domain import ClaimType
from app.core.config import settings
import google.generativeai as genai
from groq import Groq, AsyncGroq
import os

class ExplanationService:
    """
    Generates narrative explanations for verified claims.
    Supports Google Gemini (Primary) and Groq Llama 3 (Secondary).
    """
    
    def __init__(self):
        self.provider = None
        self.client = None
        
        # 1. Try Gemini
        # 1. Try Gemini
        gemini_key = settings.gemini_api_key
        print(f"DEBUG: Gemini Key from Settings: '{gemini_key}'")
        
        if gemini_key and "placeholder" not in gemini_key.lower() and not gemini_key.startswith("your_"):
            try:
                genai.configure(api_key=gemini_key)
                self.client = genai.GenerativeModel('gemini-1.5-flash')
                self.provider = "gemini"
                print("✅ Explanation Service: Connected to Gemini Pro")
            except Exception as e:
                print(f"⚠️ Gemini Init Failed: {e}")
        else:
             print("DEBUG: Gemini Key validation failed (is None, placeholder, or default).")

        # 2. Try Groq (if Gemini failed/missing/invalid)
        if not self.client and settings.groq_api_key and "placeholder" not in settings.groq_api_key.lower() and not settings.groq_api_key.startswith("your_"):
            try:
                self.client = AsyncGroq(api_key=settings.groq_api_key)
                self.provider = "groq"
                print("✅ Explanation Service: Connected to Groq (Llama 3)")
            except Exception as e:
                print(f"⚠️ Groq Init Failed: {e}")

        if not self.client:
            print("❌ Explanation Service: No valid LLM credentials found. Explanations disabled.")

    async def generate_explanation(self, claim: VerifiedClaim) -> str:
        """
        Generate a human-readable explanation for the verified claim.
        """
        if not self.client:
            return claim.evidence_summary or "Explanation unavailable (LLM disabled)."

        # Select Prompt Template
        prompt_text = self._build_prompt(claim)
        
        try:
            if self.provider == "gemini":
                response = await self.client.generate_content_async(prompt_text)
                return self._clean_output(response.text)
                
            elif self.provider == "groq":
                completion = await self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a precise, neutral fact-checking assistant. Output ONLY the summary paragraph."},
                        {"role": "user", "content": prompt_text}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.3,
                    max_tokens=150,
                )
                return self._clean_output(completion.choices[0].message.content)
                
        except Exception as e:
            print(f"LLM Generation Failed ({self.provider}): {e}")
            return claim.evidence_summary or "Detailed explanation could not be generated."

    def _build_prompt(self, claim: VerifiedClaim) -> str:
        """Construct the customized prompt based on Claim Type."""
        
        base_evidence = self._format_evidence(claim.evidence_items)
        stats = claim.strategy_stats or {}
        
        # === 1. Scientific Strategy ===
        if claim.claim_type == ClaimType.SCIENTIFIC_MEDICAL.value:
            consensus = stats.get('consensus_score', 'Unknown')
            if isinstance(consensus, float):
                consensus = f"{int(consensus * 100)}%"
                
            return f"""
            Role: Scientific Communicator.
            Task: Explain the verdict for this medical claim based ONLY on the evidence.
            
            Claim: "{claim.original_text}"
            Verdict: {claim.verdict.value}
            Scientific Consensus Score: {consensus}
            
            Evidence:
            {base_evidence}
            
            Directives:
            - If consensus is high (>80%), emphasize the scientific agreement.
            - If consensus is low or conflicting, mention the uncertainty.
            - Cite specific journals or bodies (WHO, CDC, Nature) if present in evidence.
            - Keep it under 80 words.
            """

        # === 2. Political Strategy ===
        elif claim.claim_type == ClaimType.POLITICAL_ALLEGATION.value:
            official_count = stats.get('official_sources', 0)
            polarization = stats.get('polarization', 'Unknown')
            
            return f"""
            Role: Neutral Fact-Checker.
            Task: Explain the verdict for this political claim based ONLY on the evidence.
            
            Claim: "{claim.original_text}"
            Verdict: {claim.verdict.value}
            Context: {official_count} official records found. Polarization Level: {polarization}.
            
            Evidence:
            {base_evidence}
            
            Directives:
            - Prioritize official records (.gov, legislation) over news reports.
            - If sources are split (Left vs Right), explicitly state that it is a disputed topic.
            - Remain absolutely neutral.
            - Keep it under 80 words.
            """

        # === 3. Breaking News Strategy ===
        elif claim.claim_type == ClaimType.BREAKING_EVENT.value:
            velocity = stats.get('velocity', 0)
            status = stats.get('status', 'Unknown')
            
            return f"""
            Role: Breaking News Desk.
            Task: Summarize the developing situation based ONLY on the evidence.
            
            Claim: "{claim.original_text}"
            Current Verdict: {claim.verdict.value}
            Velocity: {velocity} sources/hour. Status: {status}.
            
            Evidence:
            {base_evidence}
            
            Directives:
            - Use cautious language ("Early reports suggest...", "Details are emerging...").
            - Mention that the situation is fluid if the verdict is 'developing'.
            - Do not state unconfirmed details as absolute fact.
            - Keep it under 80 words.
            """

        # === 4. General Fallback ===
        else:
            return f"""
            Role: Fact-Checker.
            Task: Explain why this claim is {claim.verdict.value} based ONLY on the evidence.
            
            Claim: "{claim.original_text}"
            
            Evidence:
            {base_evidence}
            
            Directives:
            - Synthesize the evidence into a clear conclusion.
            - Mention the most reliable source found.
            - Keep it under 80 words.
            """

    async def explain_media(self, image_bytes: bytes, verdict: str, confidence: float) -> str:
        """
        Generate a visual explanation for media analysis using Gemini Vision.
        """
        if not self.client or self.provider != "gemini":
            return "Visual explanation unavailable (Gemini Vision required)."
            
        try:
            import PIL.Image
            import io
            image = PIL.Image.open(io.BytesIO(image_bytes))
            
            prompt = f"""
            Role: Digital Forensic Analyst.
            Task: Analyze this image and explain the verdict: {verdict} (Confidence: {confidence}%).
            
            If Verdict is FAKE:
            Look for visual artifacts, inconsistent lighting, warped backgrounds, unnatural skin textures, or mismatched reflections.
            
            If Verdict is REAL:
            Highlight the consistency of lighting, natural noise patterns, and lack of digital artifacts.
            
            Keep the explanation under 80 words. Be technical but accessible.
            """
            
            # Gemini Pro Vision call (model name might differ slightly, using auto-selection if possible or 'gemini-1.5-flash')
            # Assuming self.client is configured. For Vision we usually need 'gemini-pro-vision'.
            # However, 'gemini-1.5-flash' handles everything.
            
            # Re-initialize specific model for vision if needed, or stick to current if it's 1.5-flash.
            # Safety check: simplistic approach
            model = genai.GenerativeModel('gemini-1.5-flash') 
            response = await model.generate_content_async([prompt, image])
            return self._clean_output(response.text)
            
        except Exception as e:
            print(f"Vision Explanation Failed: {e}")
            return "Could not generate visual explanation due to API limitations."

    def _format_evidence(self, items: List[EvidenceItem]) -> str:
        """Format top 5 evidence items for the prompt."""
        if not items:
            return "No verifiable evidence found."
            
        text = ""
        for i, item in enumerate(items[:5]):
            text += f"{i+1}. [{item.source_domain}] ({item.source_type.value}): {item.text[:200]}...\n"
        return text

    def _clean_output(self, text: str) -> str:
        """Clean extra whitespace/markdown."""
        return text.replace('**', '').replace('"', '').strip()

# Singleton
_explanation_service = None

def get_explanation_service():
    global _explanation_service
    if _explanation_service is None:
        _explanation_service = ExplanationService()
    return _explanation_service
