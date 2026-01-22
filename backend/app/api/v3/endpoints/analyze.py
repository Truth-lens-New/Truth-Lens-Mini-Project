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
# Concurrency Fix
from fastapi.concurrency import run_in_threadpool
from app.services.extraction import ClaimExtractorV3
from app.services.typing import ClaimClassifier

# Database & Auth
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.check import Check


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
        "phase": 2,
        "models_loaded": ModelManager.is_initialized()
    }


# ============ Phase 2: Investigation Endpoint ============

class InvestigateRequestV3(BaseModel):
    """Request body for /v3/investigate endpoint."""
    input_type: str = Field(
        default="text",
        description="Type of input: text, url, image"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="The content to analyze and investigate"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "input_type": "text",
                "content": "COVID vaccines cause autism."
            }
        }


class EvidenceResponse(BaseModel):
    """Single evidence item in response."""
    source_domain: str
    source_type: str
    stance: str
    stance_confidence: float
    trust_score: int
    text_preview: str


class VerifiedClaimResponse(BaseModel):
    """Verified claim with verdict."""
    original_text: str
    claim_type: str
    verdict: str
    confidence: float
    evidence_summary: str
    evidence_count: int
    sources_checked: int
    investigation_time_ms: int
    evidence: List[EvidenceResponse]


class InvestigateMetadata(BaseModel):
    """Metadata about the investigation."""
    input_type: str
    total_processing_time_ms: int
    claims_found: int
    claims_verified: int
    investigated_at: datetime


class InvestigateResponseV3(BaseModel):
    """Response from /v3/investigate endpoint."""
    success: bool
    verified_claims: List[VerifiedClaimResponse]
    metadata: InvestigateMetadata


# Verdict engine (lazy init)
_verdict_engine = None


def get_verdict_engine_singleton():
    """Get or initialize verdict engine."""
    global _verdict_engine
    if _verdict_engine is None:
        from app.services.investigation import get_verdict_engine
        _verdict_engine = get_verdict_engine()
    return _verdict_engine


@router.post("/investigate", response_model=InvestigateResponseV3)
async def investigate_content(
    request: InvestigateRequestV3,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Full investigation endpoint (Phase 2).
    
    - Extracts claims from input
    - Types each claim
    - Investigates checkable claims
    - Returns verdict with evidence trail
    - SAVES result to history
    
    WARNING: This is slower than /analyze (~5-30 seconds per claim)
    as it performs actual internet research.
    """
    start_time = time.time()
    
    try:
        # Get services
        input_gateway, claim_extractor, claim_classifier = get_services()
        verdict_engine = get_verdict_engine_singleton()
        
        # Parse input type
        try:
            input_type = InputType(request.input_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid input_type: {request.input_type}"
            )
        
        # Step 1: Process input
        processed = input_gateway.process(input_type, request.content)
        
        # Step 2: Extract claims
        raw_claims = claim_extractor.extract(processed)
        
        # Step 3: Type claims
        typed_claims = claim_classifier.classify(raw_claims)
        
        # Step 4: Investigate each claim
        verified_claims = []
        for typed_claim in typed_claims:
            # PHASE 2B: Fully Async - Non-blocking on event loop
            result = await verdict_engine.verify(typed_claim)
            
            # Build evidence list for response
            evidence = [
                EvidenceResponse(
                    source_domain=e.source_domain,
                    source_type=e.source_type.value,
                    stance=e.stance.value,
                    stance_confidence=round(e.stance_confidence, 3),
                    trust_score=e.trust_score,
                    text_preview=e.text[:100] + "..." if len(e.text) > 100 else e.text
                )
                for e in result.evidence_items[:5]
            ]
            
            verified_claims.append(VerifiedClaimResponse(
                original_text=result.original_text,
                claim_type=result.claim_type,
                verdict=result.verdict.value,
                confidence=round(result.confidence, 3),
                evidence_summary=result.evidence_summary,
                evidence_count=len(result.evidence_items),
                sources_checked=result.sources_checked,
                investigation_time_ms=result.investigation_time_ms,
                evidence=evidence
            ))

            # --- Save to History (DB) ---
            if result.verdict.value != "not_checkable":
                try:
                    # Map float confidence to string label for DB
                    conf_score = result.confidence
                    conf_label = "High" if conf_score >= 0.8 else "Medium" if conf_score >= 0.5 else "Low"
                    
                    # Determine input columns
                    input_text_val = request.content if request.input_type == "text" else None
                    input_url_val = request.content if request.input_type == "url" else None

                    # Create DB record
                    db_check = Check(
                        user_id=current_user["user_id"],
                        input_text=input_text_val,
                        input_url=input_url_val,
                        claim=result.original_text,
                        verdict=result.verdict.value,
                        confidence=conf_label, # DB expects string
                        explanation=result.evidence_summary,
                        pipeline_version="3.0.0",
                        created_at=datetime.utcnow()
                    )
                    db.add(db_check)
                except Exception as e:
                    print(f"Failed to save history: {e}")
        
        # Commit all history items
        try:
            await db.commit()
        except Exception as e:
            print(f"DB Commit failed: {e}")
            await db.rollback()
        
        # Calculate total time
        total_time = int((time.time() - start_time) * 1000)
        
        metadata = InvestigateMetadata(
            input_type=input_type.value,
            total_processing_time_ms=total_time,
            claims_found=len(typed_claims),
            claims_verified=len([c for c in verified_claims 
                               if c.verdict != "not_checkable"]),
            investigated_at=datetime.now()
        )
        
        return InvestigateResponseV3(
            success=True,
            verified_claims=verified_claims,
            metadata=metadata
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")
