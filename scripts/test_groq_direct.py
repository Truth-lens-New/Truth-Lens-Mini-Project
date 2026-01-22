
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

# Mock settings loading if needed, or rely on .env loading
# We need to make sure the environment variables are loaded for the test script
from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend/.env')))

try:
    from app.core.config import settings
    print(f"DEBUG: GROQ_API_KEY from settings: {settings.groq_api_key[:10]}..." if settings.groq_api_key else "DEBUG: GROQ_API_KEY is Empty or None")
except ImportError as e:
    print(f"Error importing settings: {e}")
    sys.exit(1)

from app.services.extraction.claim_extractor_v3 import ClaimExtractorV3

print("\n--- Testing V3 Extractor ---")
extractor = ClaimExtractorV3()
if extractor.groq_client:
    print("✅ V3 Client initialized successfully")
else:
    print("❌ V3 Client failed to initialize")

print("\n--- Testing Extraction ---")
text_input = "VACCINES ARE KILLING OUR CHILDREN!!! THE GOVERNMENT IS LYING TO US ALL!!! WAKE UP SHEEPLE!!!"
print(f"Input: {text_input}")

try:
    claims = extractor._extract_with_llm(text_input)
    
    if claims:
        print(f"Extracted {len(claims)} claims:")
        for c in claims:
            print(f" - {c.text}")
    else:
        print("Result: None")
    
    if claims and len(claims) >= 2:
        print("✅ SUCCESS: Extracted sufficient claims")
    else:
        print("❌ FAILURE: Did not extract expected claims")

except Exception as e:
    print(f"❌ EXCEPTION during extraction: {e}")
