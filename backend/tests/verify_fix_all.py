
import asyncio
import sys
import os
from unittest.mock import MagicMock

# Mock heavy/missing dependencies
sys.modules["timm"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["app.services.deepfake"] = MagicMock()
sys.modules["scipy"] = MagicMock()
sys.modules["scipy.spatial"] = MagicMock()
sys.modules["scipy.spatial.distance"] = MagicMock()

# Setup mocks to survive StanceDetector logic
# We need result['labels'] and result['scores'] to be iterable lists of floats/strings
mock_pipeline_result = {
    'labels': ['SUPPORTS', 'REFUTES', 'NEUTRAL', 'discussing the myth'],
    'scores': [0.95, 0.01, 0.01, 0.03]
}
# When classifier is called, return this dict
mock_classifier = MagicMock(return_value=mock_pipeline_result)
# Configure pipeline mock
mock_transformers = MagicMock()
mock_transformers.pipeline.return_value = mock_classifier
sys.modules["transformers"] = mock_transformers


sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.input import InputGateway
from app.models.domain import InputType, ClaimType, TypedClaim
from app.services.extraction import ClaimExtractorV3
from app.services.investigation import VerdictEngine

async def verify_pipeline():
    print("🚀 Starting End-to-End Verification...")
    url = "https://www.historyextra.com/period/20th-century/did-nasa-fake-moon-landing-real-history-conspiracy/"
    
    # 1. Test Scraper (Anti-Block)
    print(f"\n1. Testing Scraper (User-Agent Fix)...")
    gateway = InputGateway()
    try:
        processed = gateway.process(InputType.URL, url)
        if len(processed.text) < 500:
             print(f"   ⚠️ Warning: Content seems short ({len(processed.text)} chars). Possible block?")
             print(f"   Preview: {processed.text}...")
        else:
             print(f"   ✅ Scraper Success! Length: {len(processed.text)} chars")
             print(f"   Preview: {processed.text[:100]}...")
    except Exception as e:
        print(f"   ❌ Scraper Failed: {e}")
        return

    # 2. Test Extractor
    print(f"\n2. Testing Extractor...")
    extractor = ClaimExtractorV3()
    claims = extractor.extract(processed)
    print(f"   ✅ Extracted {len(claims)} claims.")
    
    if not claims:
        print("   ❌ No claims found, aborting.")
        return

    # 3. Test Investigation (Async Stance Fix)
    print(f"\n3. Testing Investigation (Async Non-Blocking)...")
    
    # Manually construct a Scientific claim to force the strategy that was hanging
    print("   User Case: Forcing 'ScientificStrategy' execution")
    
    # Using the first claim found
    target_claim_text = claims[0].text
    typed_claim = TypedClaim(
        text=target_claim_text,
        claim_type=ClaimType.SCIENTIFIC_MEDICAL,
        type_confidence=0.9,
        is_checkable=True,
        evidence_strategy="Scientific consensus check",
        status="VERIFIED",
        sentence_index=0
    )
    
    engine = VerdictEngine()
    
    try:
        print(f"   Investigating: '{typed_claim.text}'...")
        # This will call ScientificStrategy -> PubMed (Mocked/Real?) -> StanceDetector
        # PubMedSearcher uses httpx, we haven't mocked that, so it might make real calls!
        # That's good, we want to test real network except for ML.
        
        result = await engine.verify(typed_claim)
        
        print(f"   ✅ Investigation Complete!")
        print(f"   Verdict: {result.verdict}")
        print(f"   Sources Checked: {result.evidence.sources_checked}")
        print(f"   Reason: {result.reason}")
        
    except Exception as e:
        print(f"   ❌ Investigation Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_pipeline())
