"""
Real Verification Script for V3 Visual Forensics Strategy (Running in Docker)
"""

import asyncio
import base64
import os
import sys
from pathlib import Path

# Add backend to path (usually /app in Docker)
sys.path.append("/app")

from app.models.domain import InputType, ProcessedInput, RawClaim, TypedClaim, ClaimType
from app.models.evidence import Verdict
from app.services.investigation.strategies.visual import VisualForensicsStrategy
from app.services.investigation.strategies.base import InvestigationContext, InvestigationDepth

async def test_visual_strategy():
    print("🚀 Starting Real V3 Visual Forensics Strategy Test...")
    
    # 1. Create a dummy image (1x1 transparent pixel)
    dummy_png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
    
    # 2. Setup Context
    claim = TypedClaim(
        text="Visual Content Analysis",
        claim_type=ClaimType.VISUAL_MANIPULATION,
        type_confidence=1.0,
        is_checkable=True,
        evidence_strategy="Visual forensics & deepfake detection pipeline",
        status="Pending",
        raw_data=dummy_png
    )
    
    ctx = InvestigationContext(claim=claim, required_depth=InvestigationDepth.DEEP)
    
    # 3. Execute Strategy
    strategy = VisualForensicsStrategy()
    print("Running strategy.execute() (this will load ML models)...")
    result = await strategy.execute(ctx)
    
    # 4. Verify Results
    print("\n--- Strategy Result ---")
    print(f"Verdict: {result.verdict}")
    print(f"Confidence: {result.confidence_score}")
    print(f"Reason (Narrative): {result.reason[:200]}...")
    print(f"Evidence Items: {len(result.evidence.items)}")
    print(f"Strategy Stats: {list(result.strategy_stats.keys())}")
    
    if "heatmap" in result.strategy_stats:
        print("✅ Heatmap generated successfully.")
    
    if result.reason and len(result.reason) > 50:
        print("✅ Narrative explanation generated successfully.")

if __name__ == "__main__":
    asyncio.run(test_visual_strategy())
