
import sys
import os
from unittest.mock import MagicMock

# Mock unrelated heavy dependencies
sys.modules["timm"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["app.services.deepfake"] = MagicMock()

sys.path.append(os.path.join(os.getcwd(), "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), "backend/.env"))

from app.models.domain import ProcessedInput, InputType
from app.services.extraction.crux_extractor import CruxExtractor

def test_crux():
    print("🧠 Testing Crux Extraction with Gemini 2.5 Flash...")
    
    # Simulating the Moon Landing article text (partial)
    text = """
    Did NASA fake the Moon landing? The real history that debunks the conspiracy.
    Was Neil Armstrong’s “one small step for man” made not on the surface of the Moon, but on a secret, earth-bound set? 
    In the fifth episode of our podcast series Conspiracy, Rob Attar speaks to Francis French about the claims that NASA duped the entire world.
    
    One common claim is that the shadows in the photos are non-parallel, suggesting studio lighting. 
    Another is that the flag appears to flap in the wind, which is impossible in a vacuum.
    Also, conspiracy theorists point out that no stars are visible in the sky in the Apollo photographs.
    Some even claim Stanley Kubrick directed the footage.
    However, scientists explain that the flag had a stiffening rod, causing it to ripple when touched, and stars are too faint to be seen with the exposure settings used for the bright lunar surface.
    """
    
    extractor = CruxExtractor()
    if not extractor.enabled:
        print("❌ CruxExtractor disabled (API Key issue?)")
        return

    print(f"Input text length: {len(text)} chars")
    claims = extractor.extract(text, max_claims=5)
    
    print(f"\n✅ Extracted {len(claims)} Core Claims:")
    for i, c in enumerate(claims):
        print(f" {i+1}. {c.text}")

if __name__ == "__main__":
    test_crux()
