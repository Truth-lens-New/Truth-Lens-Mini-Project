"""
Visual Forensics Strategy (V3)

Verifies visual claims using deepfake detection and metadata analysis.
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.domain import ClaimType, TypedClaim
from app.models.evidence import (
    EvidenceCollection, EvidenceItem, EvidenceType, Stance, Verdict
)
from app.services.investigation.strategies.base import (
    InvestigationStrategy, InvestigationContext, InvestigationResult
)
from app.services.deepfake import get_deepfake_detector
from app.services.investigation.explanation import get_explanation_service

class VisualForensicsStrategy(InvestigationStrategy):
    """
    Strategy for analyzing images for deepfakes and manipulation.
    Integrates EfficientNet-B3 model and metadata forensic checks.
    """
    
    async def execute(self, ctx: InvestigationContext) -> InvestigationResult:
        """
        Execute visual forensic analysis.
        """
        start_time = time.time()
        claim = ctx.claim
        
        # 1. Ensure we have raw data
        if not claim.raw_data:
            return InvestigationResult(
                verdict=Verdict.NOT_CHECKABLE,
                confidence_score=0.1,
                evidence=EvidenceCollection(
                    items=[],
                    override_reason="No raw image data found for visual analysis."
                ),
                reason="Analysis requires raw image bytes."
            )
            
        # 2. Get Deepfake Detector
        try:
            detector = get_deepfake_detector()
            # Since predict is synchronous but heavy, we should ideally run it in a threadpool
            # but deepfake.py already provides analyze_image_for_deepfake which does that.
            # However, for strategy execution, we call the detector directly or via the helper.
            from app.services.deepfake import analyze_image_for_deepfake
            result = await analyze_image_for_deepfake(claim.raw_data)
        except Exception as e:
            print(f"Deepfake detection failed: {e}")
            return InvestigationResult(
                verdict=Verdict.UNVERIFIED,
                confidence_score=0.0,
                evidence=EvidenceCollection(items=[]),
                reason=f"Forensic engine error: {str(e)}"
            )

        # 3. Process Result into EvidenceCollection
        evidence = EvidenceCollection()
        
        # Map result verdict to V3 Verdict
        v3_verdict = Verdict.VERIFIED_FALSE if result["verdict"] == "FAKE" else Verdict.VERIFIED_TRUE
        
        # Add technical evidence points as EvidenceItems
        for point in result.get("evidence", []):
            evidence.add(EvidenceItem(
                text=point,
                source_url="internal://forensic-model",
                source_domain="forensics.truthlens",
                source_type=EvidenceType.FACT_CHECK,
                stance=Stance.REFUTES if result["verdict"] == "FAKE" else Stance.SUPPORTS,
                stance_confidence=result["confidence"] / 100.0,
                trust_score=90 # High trust for internal specialized model
            ))
            
        # 4. Generate Narrative Explanation (the "Inner Voice")
        explanation_service = get_explanation_service()
        try:
            # We pass the results to the explanation service for a detailed narrative
            narrative = await explanation_service.explain_media(
                image_bytes=claim.raw_data,
                verdict=result["verdict"],
                confidence=result["confidence"],
                metadata=result.get("metadata", {}),
                evidence_points=result.get("evidence", [])
            )
        except Exception as e:
            print(f"Narrative generation failed: {e}")
            narrative = "Technical analysis complete. " + " ".join(result.get("evidence", []))

        # 5. Build Final Result
        processing_time = int((time.time() - start_time) * 1000)
        evidence.investigation_time_ms = processing_time
        
        return InvestigationResult(
            verdict=v3_verdict,
            confidence_score=result["confidence"] / 100.0,
            evidence=evidence,
            reason=narrative,
            strategy_stats={
                "model": result.get("model", "EfficientNet-B3"),
                "probabilities": {
                    "real": result.get("real_probability"),
                    "fake": result.get("fake_probability")
                },
                "metadata_risk": result.get("metadata_risk_score"),
                "heatmap": result.get("heatmap"),
                "metadata": result.get("metadata", {})
            }
        )
