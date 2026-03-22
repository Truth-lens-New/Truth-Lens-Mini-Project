
import asyncio
import sys
import os
import time


# Point to backend
sys.path.append(os.path.join(os.getcwd(), "backend"))

# MOCK HEAVY LIBS
from unittest.mock import MagicMock
sys.modules["timm"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["app.services.deepfake"] = MagicMock()
sys.modules["scipy"] = MagicMock()
sys.modules["scipy.spatial"] = MagicMock()

# Load Env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), "backend/.env"))

# Import Services
from app.services.input.url_scraper import URLScraper
from app.models.domain import ProcessedInput, InputType
from app.services.extraction import ClaimExtractorV3
from app.services.typing import ClaimClassifier
from app.services.investigation import VerdictEngine
from app.models.domain import ClaimType

async def run_simulation():
    print("🚀 STARTING PRODUCTION SIMULATION")
    url = "https://www.historyextra.com/period/20th-century/did-nasa-fake-moon-landing-real-history-conspiracy/"
    
    # 1. SCRAPER
    print(f"\n[1] SCRAPING: {url}")
    scraper = URLScraper()
    try:
        processed = scraper.process(url)
        print(f"✅ Scraped {len(processed.text)} chars.")
        # print(f"Preview: {processed.text[:200]}...")
    except Exception as e:
        print(f"❌ Scraper Failed: {e}")
        return

    # 2. EXTRACTION (CRUX)
    print(f"\n[2] EXTRACTING CLAIMS (Crux Mode)...")
    extractor = ClaimExtractorV3()
    try:
        # We explicitly call extract_crux as the API would for URL
        claims = extractor.extract_crux(processed)
        print(f"✅ Extracted {len(claims)} claims.")
        for i, c in enumerate(claims):
            print(f"   {i+1}. {c.text}")
    except Exception as e:
        print(f"❌ Extraction Failed: {e}")
        return
        
    if not claims:
        print("❌ No claims extracted. Stopping.")
        return

    # 3. TYPING
    print(f"\n[3] TYPING CLAIMS...")
    classifier = ClaimClassifier()
    try:
        # Run classification (sync in this script, but async in API)
        typed_claims = classifier.classify(claims)
        print(f"✅ Typed {len(typed_claims)} claims.")
        for tc in typed_claims:
            print(f"   - {tc.text[:50]}... -> {tc.claim_type} (Checkable: {tc.is_checkable})")
    except Exception as e:
         print(f"❌ Typing Failed: {e}")
         return

    # 4. INVESTIGATION
    print(f"\n[4] INVESTIGATION (Parallel async)...")
    engine = VerdictEngine()
    
    async def investigate_one(tc):
        if not tc.is_checkable:
            return None
        print(f"   🔎 Investigating: {tc.text[:40]}...")
        try:
            result = await engine.verify(tc)
            print(f"      ✅ VERDICT for '{tc.text[:20]}...': {result.verdict}")
            return result
        except Exception as e:
            print(f"      ❌ FAILED for '{tc.text[:20]}...': {e}")
            return None

    tasks = [investigate_one(tc) for tc in typed_claims]
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start_time
    
    valid_results = [r for r in results if r]
    
    print(f"\n[5] SUMMARY")
    print(f"✅ Finished in {duration:.2f} seconds")
    print(f"Total Verified: {len(valid_results)}")
    
    for res in valid_results:
        print(f" - {res.original_text[:50]}... : {res.verdict} (Conf: {res.confidence})")

if __name__ == "__main__":
    try:
        asyncio.run(run_simulation())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
