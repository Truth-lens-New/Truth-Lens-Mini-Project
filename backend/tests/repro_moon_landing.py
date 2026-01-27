
import asyncio
import sys
import os
from unittest.mock import MagicMock

# Mock heavy dependencies
sys.modules["timm"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["app.services.deepfake"] = MagicMock()

sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.input import InputGateway
from app.models.domain import InputType, ClaimType
from app.services.extraction import ClaimExtractorV3
# We need to mock the searcher as well if we don't want to make real network calls, 
# but for a hang, we might want to see if real calls are the issue. 
# However, let's start by seeing if we can even extract claims from the URL.

async def repro():
    print("Testing URL processing...")
    url = "https://www.historyextra.com/period/20th-century/did-nasa-fake-moon-landing-real-history-conspiracy/"
    
    gateway = InputGateway()
    extractor = ClaimExtractorV3()
    
    try:
        print(f"1. Scraping URL: {url}")
        # this might block if scraper is slow
        processed = gateway.process(InputType.URL, url)
        print(f"Search completed. Scraped length: {len(processed.text)}")
        print(f"Scraped preview: {processed.text[:200]}...")
        
        print("2. Extracting claims...")
        claims = extractor.extract(processed)
        print(f"Extracted {len(claims)} claims.")
        print(f"Extracted {len(claims)} claims.")
        for i, c in enumerate(claims[:5]):
            print(f" - [{i}] {c.text}")
        
        print("\n3. Running Verdict Engine (Investigation)...")
        # Now we need to actually run the investigation to hit the hang
        from app.services.investigation import InvestigationOrchestrator, VerdictEngine
        from app.services.typing import ClaimClassifier
        
        # We need to type the claims first
        classifier = ClaimClassifier()
        typed_claims = classifier.classify(claims[:5]) # just test top 5 to save time/avoid flood
        
        engine = VerdictEngine()
        
        print(f"Investigating {len(typed_claims)} claims...")
        
        # FORCE override the first claim to be checkable to trigger the strategy
        if typed_claims:
             print("⚠️ FORCING first claim to be SCIENTIFIC_MEDICAL to trigger strategy...")
             typed_claims[0].claim_type = ClaimType.SCIENTIFIC_MEDICAL
             typed_claims[0].is_checkable = True

        for tc in typed_claims:
            print(f" -- Checking: {tc.text[:50]}... ({tc.claim_type})")
            if tc.is_checkable:
                result = await engine.verify(tc)
                print(f"    Verdict: {result.verdict} (Conf: {result.confidence})")
            else:
                print("    Skipped (not checkable)")
                
        print("\n✅ Reproduction finished successfully (No Hang).")

    except Exception as e:
        print(f"\n❌ FAILED during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(repro())
