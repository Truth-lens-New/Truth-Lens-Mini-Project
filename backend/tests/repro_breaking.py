
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.investigation.orchestrator import InvestigationOrchestrator
from app.models.domain import TypedClaim, ClaimType

async def test_breaking_news():
    print("🚀 Initializing Orchestrator...")
    orchestrator = InvestigationOrchestrator()
    
    # Using a topic likely to have recent news/activity
    claim = TypedClaim(
        text="Significant earthquake in Japan today",
        claim_type=ClaimType.BREAKING_EVENT,
        type_confidence=0.9,
        is_checkable=True,
        evidence_strategy="Breaking news check",
        status="active"
    )
    
    print(f"🔍 Investigating: '{claim.text}'...")
    evidence = await orchestrator.investigate(claim)
    
    print("\n--- RESULTS ---")
    print(f"Investigation Time: {evidence.investigation_time_ms}ms")
    print(f"Sources Checked: {evidence.sources_checked}")
    print(f"Items Collected: {len(evidence.items)}")
    print(f"Stop Reason: {evidence.stop_reason or 'None'}")
    
    if evidence.sources_checked > 0 and (len(evidence.items) > 0 or evidence.stop_reason is None):
        print("\n✅ SUCCESS: Generic/Breaking strategy is fetching sources!")
    else:
        print("\n❌ FAILURE: No sources found or error occurred.")

if __name__ == "__main__":
    asyncio.run(test_breaking_news())
