import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.investigation.orchestrator import InvestigationOrchestrator
from app.models.domain import TypedClaim, ClaimType
from app.models.evidence import EvidenceCollection

async def test_strategies():
    print("Initializing Orchestrator...")
    orchestrator = InvestigationOrchestrator()
    
    # MOCK Phase 1 to force Phase 2 (Strategies)
    orchestrator.misinfo_checker.check = MagicMock(return_value=None)
    orchestrator.wikidata_verifier.quick_fact_check = AsyncMock(return_value=None)
    orchestrator.google_factchecker.search = AsyncMock(return_value=[]) # Returns empty list
    
    # Test Cases
    claims = [
        # 1. Scientific
        TypedClaim(
            text="Vitamin D supplements prevent COVID-19 infection.",
            claim_type=ClaimType.SCIENTIFIC_MEDICAL,
            type_confidence=0.9,
            is_checkable=True,
            evidence_strategy="Scientific consensus check",
            status="active"
        ),
        # 2. Political
        TypedClaim(
            text="The government increased taxes on middle class by 50% last year.",
            claim_type=ClaimType.POLITICAL_ALLEGATION,
            type_confidence=0.9,
            is_checkable=True,
            evidence_strategy="Multi-source verification",
            status="active"
        ),
        # 3. Breaking
        TypedClaim(
            text="Earthquake reported in Japan just now.",
            claim_type=ClaimType.BREAKING_EVENT,
            type_confidence=0.9,
            is_checkable=True,
            evidence_strategy="Breaking news check",
            status="active"
        ),
        # 4. Generic
        TypedClaim(
            text="The Eiffel Tower is in London.",
            claim_type=ClaimType.FACTUAL_STATEMENT,
            type_confidence=0.9,
            is_checkable=True,
            evidence_strategy="General web check",
            status="active"
        )
    ]
    
    for claim in claims:
        print(f"\n--- Testing Claim: {claim.text} ({claim.claim_type}) ---")
        try:
            evidence = await orchestrator.investigate(claim)
            print(f"Sources Checked: {evidence.sources_checked}")
            print(f"Items Found: {len(evidence.items)}")
            if evidence.override_verdict:
                print(f"OVERRIDE VERDICT: {evidence.override_verdict}")
                print(f"Reason: {evidence.override_reason}")
            else:
                print("No Override Verdict (Generic/Standard synthesis needed)")
            
            for i, item in enumerate(evidence.items[:3]):
                print(f"  [{i+1}] {item.source_domain}: {item.stance} ({item.text[:50]}...)")
                
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_strategies())
