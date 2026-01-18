"""
TruthLens V3 Analyze Endpoint

Phase 1: Extract claims, type them, return with pending status.
"""

import time
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.models.domain import InputType, ClaimType
from app.services.input import InputGateway
from app.services.extraction import ClaimExtractorV3
from app.services.typing import ClaimClassifier


router = APIRouter()


# ============ Request/Response Models ============

class AnalyzeRequestV3(BaseModel):
    """Request body for /v3/analyze endpoint."""
    input_type: str = Field(
        default="text",
        description="Type of input: text, url, image, social"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="The content to analyze"
    )
    options: Optional[dict] = Field(
        default=None,
        description="Optional processing options"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "input_type": "text",
                "content": "COVID vaccines cause autism. The weather is nice today.",
                "options": None
            }
        }


class ClaimResponse(BaseModel):
    """Single claim in response."""
    original_text: str
    claim_type: str
    type_confidence: float
    is_checkable: bool
    evidence_strategy: str
    status: str


class AnalysisMetadata(BaseModel):
    """Metadata about the analysis."""
    input_type: str
    processing_time_ms: int
    claims_found: int
    checkable_claims: int
    analyzed_at: datetime


class AnalyzeResponseV3(BaseModel):
    """Response from /v3/analyze endpoint."""
    success: bool
    claims: List[ClaimResponse]
    metadata: AnalysisMetadata


# ============ Services (Lazy Initialization) ============

_input_gateway = None
_claim_extractor = None
_claim_classifier = None


def get_services():
    """Get or initialize services."""
    global _input_gateway, _claim_extractor, _claim_classifier
    
    if _input_gateway is None:
        _input_gateway = InputGateway()
    if _claim_extractor is None:
        _claim_extractor = ClaimExtractorV3()
    if _claim_classifier is None:
        _claim_classifier = ClaimClassifier()
    
    return _input_gateway, _claim_extractor, _claim_classifier


# ============ Endpoints ============

@router.post("/analyze", response_model=AnalyzeResponseV3)
def analyze_content(request: AnalyzeRequestV3):
    """
    Analyze content for claims (Phase 1).
    
    - Extracts claims from input
    - Types each claim
    - Returns with pending status (no verdict yet)
    
    This is the honest Phase 1 skeleton - we tell users what we found
    and what we WOULD check, but don't fake any verdicts.
    """
    start_time = time.time()
    
    try:
        # Get services
        input_gateway, claim_extractor, claim_classifier = get_services()
        
        # Parse input type
        try:
            input_type = InputType(request.input_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid input_type: {request.input_type}. Valid: text, url, image, social"
            )
        
        # Step 1: Process input
        processed = input_gateway.process(input_type, request.content)
        
        # Step 2: Extract claims
        raw_claims = claim_extractor.extract(processed)
        
        # Step 3: Type claims
        typed_claims = claim_classifier.classify(raw_claims)
        
        # Step 4: Build response
        processing_time = int((time.time() - start_time) * 1000)
        
        claims_response = [
            ClaimResponse(
                original_text=c.text,
                claim_type=c.claim_type.value,
                type_confidence=round(c.type_confidence, 3),
                is_checkable=c.is_checkable,
                evidence_strategy=c.evidence_strategy,
                status=c.status
            )
            for c in typed_claims
        ]
        
        metadata = AnalysisMetadata(
            input_type=input_type.value,
            processing_time_ms=processing_time,
            claims_found=len(typed_claims),
            checkable_claims=sum(1 for c in typed_claims if c.is_checkable),
            analyzed_at=datetime.now()
        )
        
        return AnalyzeResponseV3(
            success=True,
            claims=claims_response,
            metadata=metadata
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/health")
def health_check():
    """Health check for V3 API."""
    from app.services.models import ModelManager
    return {
        "status": "healthy",
        "version": "3.0.0",
        "phase": 1,
        "models_loaded": ModelManager.is_initialized()
    }
