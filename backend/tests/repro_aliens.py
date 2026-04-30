
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.investigation.orchestrator import InvestigationOrchestrator
from app.models.domain import TypedClaim, ClaimType

async def test_aliens_claim():
    print("🚀 Initializing Orchestrator...")
    orchestrator = InvestigationOrchestrator()
    
    claim = TypedClaim(
        text="Aliens are real",
        claim_type=ClaimType.FACTUAL_STATEMENT,
        type_confidence=0.9,
        is_checkable=True,
        evidence_strategy="General web check",
        status="active"
    )
    
    print(f"🔍 Investigating: '{claim.text}'...")
    evidence = await orchestrator.investigate(claim)
    
    print("\n--- RESULTS ---")
    print(f"Investigation Time: {evidence.investigation_time_ms}ms")
    print(f"Sources Checked: {evidence.sources_checked}")
    print(f"Items Collected: {len(evidence.items)}")
    print(f"Stop Reason: {evidence.stop_reason or 'None'}")
    
    if evidence.override_verdict:
        print(f"Verdict: {evidence.override_verdict} (Confidence: {evidence.override_confidence})")
        print(f"Reason: {evidence.override_reason}")
    
    if evidence.sources_checked > 0 and evidence.investigation_time_ms > 0:
        print("\n✅ SUCCESS: Pipeline is alive and checking sources!")
    else:
        print("\n❌ FAILURE: Pipeline still reporting 0 sources or 0ms.")

if __name__ == "__main__":
    asyncio.run(test_aliens_claim())
