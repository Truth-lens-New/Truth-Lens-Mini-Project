import asyncio
import sys
import os
from unittest.mock import MagicMock

# Mock deep learning dependencies that might be missing in test env
sys.modules["timm"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["app.services.deepfake"] = MagicMock()

# Adjust path to import app correctly
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.models.domain import TypedClaim, ClaimType
from app.services.investigation.strategies.political import PoliticalStrategy
from app.services.investigation.strategies.base import InvestigationContext

# Mock Searcher to inspect queries
class MockSearcher:
    async def search(self, query, max_results=5):
        print(f"[TEST] Mock Search Query: {query}")
        return []

# Mock Wikidata to avoid network calls
class MockWikidata:
    async def quick_fact_check(self, claim):
        return None

async def test_political_strategy():
    print("Testing PoliticalStrategy localization...")
    
    strategy = PoliticalStrategy()
    
    # Inject mocks
    strategy.searcher = MockSearcher()
    strategy.wikidata_verifier = MockWikidata()
    
    # helper
    def create_claim(text):
        return TypedClaim(
            text=text, 
            claim_type=ClaimType.POLITICAL_ALLEGATION,
            type_confidence=1.0,
            is_checkable=True,
            evidence_strategy="political",
            status="pending"
        )
    
    # Test Case 1: US Claim
    print("\n--- Test Case 1: US Claim ---")
    claim_us = create_claim("Joe Biden won the 2020 election.")
    ctx_us = InvestigationContext(claim=claim_us, timestamp=None, required_depth=None, known_evidence=None)
    
    # We just want to trigger the search query construction
    await strategy.execute(ctx_us)
    
    # Test Case 2: India Claim
    print("\n--- Test Case 2: India Claim ---")
    claim_in = create_claim("Modi implemented new tax laws in Delhi.")
    ctx_in = InvestigationContext(claim=claim_in, timestamp=None, required_depth=None, known_evidence=None)
    
    await strategy.execute(ctx_in)

    # Test Case 3: UK Claim
    print("\n--- Test Case 3: UK Claim ---")
    claim_uk = create_claim("UK Parliament passed the Brexit bill.")
    ctx_uk = InvestigationContext(claim=claim_uk, timestamp=None, required_depth=None, known_evidence=None)
    
    await strategy.execute(ctx_uk)

if __name__ == "__main__":
    asyncio.run(test_political_strategy())
