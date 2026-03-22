
import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add backend to path
# Add current directory to path (in Docker /app is the root)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.temporal.time_context import get_time_context_service
from app.models.evidence import VerifiedClaim, EvidenceItem, EvidenceType, Stance, Verdict
from app.models.domain import TemporalState

def create_mock_claim(text: str, evidence_dates: list) -> VerifiedClaim:
    """Helper to create a VerifiedClaim with evidence carrying specific dates."""
    evidence_items = []
    for dt in evidence_dates:
        date_str = dt.strftime("%Y-%m-%d")
        evidence_items.append(EvidenceItem(
            text=f"Evidence found on {date_str} regarding {text}",
            source_domain="news.com",
            source_type=EvidenceType.NEWS_ARTICLE,
            source_url="http://example.com",
            retrieved_at=dt,
            stance=Stance.SUPPORTS,
            stance_confidence=0.9,
            trust_score=80
        ))
        
    return VerifiedClaim(
        original_text=text,
        claim_type="test",
        verdict=Verdict.VERIFIED_TRUE,
        confidence=1.0,
        evidence_summary="Summary",
        evidence_items=evidence_items,
        sources_checked=1,
        investigation_time_ms=100
    )

def test_temporal_logic():
    print("⏳ Testing Time Context Service...")
    service = get_time_context_service()
    now = datetime.now()
    
    # Test 1: Developing (Evidence < 24h old)
    print("\n[Test 1] Developing Story")
    claim1 = create_mock_claim(
        "Breaking news happened", 
        [now - timedelta(hours=2)]
    )
    ctx1 = service.analyze(claim1)
    print(f"   State: {ctx1.state.value}")
    print(f"   Freshness: {ctx1.evidence_freshness_hours:.1f} hours")
    
    if ctx1.state == TemporalState.DEVELOPING:
        print("✅ PASS: Correctly identified as DEVELOPING")
    else:
        print(f"❌ FAIL: Expected DEVELOPING, got {ctx1.state}")

    # Test 2: Stabilized (Evidence > 1 month old)
    print("\n[Test 2] Stabilized Fact")
    claim2 = create_mock_claim(
        "Old fact", 
        [now - timedelta(days=45)]
    )
    ctx2 = service.analyze(claim2)
    print(f"   State: {ctx2.state.value}")
    
    if ctx2.state == TemporalState.STABILIZED:
        print("✅ PASS: Correctly identified as STABILIZED")
    else:
        print(f"❌ FAIL: Expected STABILIZED, got {ctx2.state}")

    # Test 3: Historical (Evidence > 1 year old)
    print("\n[Test 3] Historical Event")
    claim3 = create_mock_claim(
        "Ancient history", 
        [now - timedelta(days=400)]
    )
    ctx3 = service.analyze(claim3)
    print(f"   State: {ctx3.state.value}")
    
    if ctx3.state == TemporalState.HISTORICAL:
        print("✅ PASS: Correctly identified as HISTORICAL")
    else:
        print(f"❌ FAIL: Expected HISTORICAL, got {ctx3.state}")

if __name__ == "__main__":
    test_temporal_logic()
