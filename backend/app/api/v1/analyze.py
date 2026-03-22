"""
TruthLens Analyze API v1

Main analysis endpoint that orchestrates the full verification pipeline.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.check import Check
from app.services import (
    score_domain,
    extract_claims,
    search_factchecks,
    search_news,
    classify_all_stances,
    weighted_stance,
    aggregate_verdict,
    generate_explanation,
    llm_assess_claim,
    analyze_image_for_deepfake,
)


router = APIRouter(prefix="/api/v1", tags=["Analysis"])


# Request/Response Schemas
class AnalyzeRequest(BaseModel):
    """Analysis request payload."""
    text: Optional[str] = Field(None, description="Claim or article text to analyze")
    url: Optional[str] = Field(None, description="URL of the article to analyze")
    language: str = Field("en", description="Language code")


class DomainTrustResponse(BaseModel):
    """Domain trust information."""
    domain: Optional[str]
    score: str
    category: Optional[str] = "unknown"


class FactCheckResponse(BaseModel):
    """Fact-check result."""
    found: bool
    rating: Optional[str]
    summary: Optional[str]
    source: Optional[str]
    url: Optional[str]


class EvidenceItem(BaseModel):
    """Single evidence item."""
    title: str
    description: str
    domain: Optional[str]
    url: Optional[str]
    source: Optional[str]
    stance: str


class StanceSummary(BaseModel):
    """Stance analysis summary."""
    supports: int = 0
    refutes: int = 0
    discuss: int = 0
    unrelated: int = 0


class AnalyzeResponse(BaseModel):
    """Full analysis response."""
    claim: Optional[str]
    verdict: str
    confidence: str
    domain_trust: DomainTrustResponse
    factcheck: FactCheckResponse
    evidence: list[EvidenceItem]
    stance_summary: StanceSummary
    explanation: str


# Claim extraction response for user confirmation
class ExtractClaimRequest(BaseModel):
    """Request for claim extraction only."""
    text: Optional[str] = Field(None, description="Text to extract claim from")
    url: Optional[str] = Field(None, description="URL to extract claim from")


class ExtractClaimResponse(BaseModel):
    """Response with extracted claim for user confirmation."""
    primary_claim: Optional[str]
    candidates: list[str]
    message: str


@router.post("/extract-claim", response_model=ExtractClaimResponse)
async def extract_claim_endpoint(
    request: ExtractClaimRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Extract claims from text for user confirmation before full analysis.
    
    This is STEP 3 of the pipeline - allows user to confirm/edit the claim
    before running the expensive full analysis.
    """
    if not request.text and not request.url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either text or url must be provided"
        )
    
    input_text = request.text or ""
    
    # If URL provided but no text
    if request.url and not input_text:
        input_text = f"Content from: {request.url}"
    
    # Extract claims using spaCy + Gemini
    claim_result = await extract_claims(input_text)
    primary_claim = claim_result.get('primary_claim')
    candidates = claim_result.get('refined_claims', [])
    
    if not primary_claim and not candidates:
        return ExtractClaimResponse(
            primary_claim=input_text[:500] if input_text else None,
            candidates=[],
            message="Could not extract a specific claim. Using the provided text as-is."
        )
    
    return ExtractClaimResponse(
        primary_claim=primary_claim,
        candidates=candidates,
        message="We detected this claim. Please confirm or edit before analysis."
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_claim(
    request: AnalyzeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze a claim or URL for misinformation.
    
    Pipeline:
    1. Domain trust scoring (if URL provided)
    2. Claim extraction (spaCy + Gemini)
    3. Fact-check lookup (Google Fact Check API)
    4. Evidence retrieval (GNews API)
    5. Stance classification (Gemini)
    6. Verdict aggregation (deterministic rules)
    7. Explanation generation (Gemini)
    
    Args:
        request: Analysis request with text and/or URL
        current_user: Authenticated user from JWT
        db: Database session
        
    Returns:
        Full analysis response
    """
    # Validate input
    if not request.text and not request.url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either text or url must be provided"
        )
    
    # Step 1: Domain Trust
    domain_trust = score_domain(request.url)
    
    # Step 2: Claim Extraction
    input_text = request.text or ""
    
    # If URL provided but no text, use URL for claim extraction
    # In production, you'd fetch the URL content here
    if request.url and not input_text:
        input_text = f"Content from: {request.url}"
    
    claim_result = await extract_claims(input_text)
    primary_claim = claim_result.get('primary_claim')
    
    if not primary_claim:
        # Use the input text as the claim if extraction fails
        primary_claim = input_text[:500] if input_text else "Unknown claim"
    
    # Step 3: Fact Check
    factcheck_result = await search_factchecks(primary_claim)
    
    # Step 4: Evidence Retrieval
    news_articles = await search_news(primary_claim, max_results=5)
    
    # Step 5: Stance Classification
    articles_with_stance = await classify_all_stances(primary_claim, news_articles)
    stance_summary = weighted_stance(articles_with_stance)
    
    # Step 6: Verdict Aggregation
    verdict_result = aggregate_verdict(
        factcheck_result=factcheck_result,
        stance_summary=stance_summary,
        domain_trust=domain_trust
    )
    
    # Step 6b: LLM Fallback for inconclusive verdicts
    # If no clear verdict from fact-checks/evidence, use LLM to assess obvious claims
    if verdict_result.get('basis') in ['insufficient_evidence', 'mixed_evidence']:
        llm_result = await llm_assess_claim(primary_claim)
        if llm_result.get('used') and llm_result.get('verdict'):
            # LLM provided a verdict - use it but mark confidence appropriately
            verdict_result = {
                'verdict': llm_result['verdict'],
                'confidence': llm_result.get('confidence', 'medium'),
                'basis': 'llm_assessment'
            }
    
    # Step 7: Explanation Generation
    explanation = await generate_explanation({
        'claim': primary_claim,
        'verdict': verdict_result['verdict'],
        'confidence': verdict_result['confidence'],
        'factcheck': factcheck_result,
        'stance_summary': stance_summary,
        'domain_trust': domain_trust
    })
    
    # Step 8: Save to Database
    check = Check(
        user_id=current_user['user_id'],
        input_text=request.text,
        input_url=request.url,
        claim=primary_claim,
        domain_score=domain_trust.get('score'),
        factcheck_rating=factcheck_result.get('rating'),
        factcheck_summary=factcheck_result.get('summary'),
        stance_summary=stance_summary,
        verdict=verdict_result['verdict'],
        confidence=verdict_result['confidence'],
        explanation=explanation,
        pipeline_version=settings.pipeline_version
    )
    
    db.add(check)
    await db.commit()
    
    # Build response
    counts = stance_summary.get('counts', {})
    
    return AnalyzeResponse(
        claim=primary_claim,
        verdict=verdict_result['verdict'],
        confidence=verdict_result['confidence'],
        domain_trust=DomainTrustResponse(
            domain=domain_trust.get('domain'),
            score=domain_trust.get('score', 'unknown'),
            category=domain_trust.get('category', 'unknown')
        ),
        factcheck=FactCheckResponse(
            found=factcheck_result.get('found', False),
            rating=factcheck_result.get('rating'),
            summary=factcheck_result.get('summary'),
            source=factcheck_result.get('source'),
            url=factcheck_result.get('url')
        ),
        evidence=[
            EvidenceItem(
                title=article.get('title', ''),
                description=article.get('description', ''),
                domain=article.get('domain'),
                url=article.get('url'),
                source=article.get('source'),
                stance=article.get('stance', 'UNRELATED')
            )
            for article in articles_with_stance
        ],
        stance_summary=StanceSummary(
            supports=counts.get('SUPPORTS', 0),
            refutes=counts.get('REFUTES', 0),
            discuss=counts.get('DISCUSS', 0),
            unrelated=counts.get('UNRELATED', 0)
        ),
        explanation=explanation
    )

# Media Analysis Response Schema
class MediaAnalysisResponse(BaseModel):
    """Response for media (image/video) analysis."""
    verdict: str = Field(..., description="FAKE or REAL")
    confidence: float = Field(..., description="Confidence percentage (0-100)")
    confidence_level: str = Field(..., description="high, medium, or low")
    real_probability: float = Field(..., description="Probability of being real (0-100)")
    fake_probability: float = Field(..., description="Probability of being fake (0-100)")
    model: str = Field(..., description="Model used for detection")
    metadata: dict = Field(default={}, description="Image metadata (EXIF, format, etc.)")
    evidence: list = Field(default=[], description="Evidence points supporting the verdict")
    heatmap: Optional[str] = Field(default=None, description="Base64 encoded Grad-CAM heatmap")


@router.post("/analyze-media", response_model=MediaAnalysisResponse)
async def analyze_media(
    file: UploadFile = File(..., description="Image file to analyze"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze an uploaded image for deepfake detection.
    
    Uses EfficientNet-B0 model trained on deepfake datasets.
    
    Args:
        file: Image file (JPEG, PNG, etc.)
        current_user: Authenticated user from JWT
        
    Returns:
        MediaAnalysisResponse with verdict and confidence scores
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp", "video/mp4", "video/quicktime", "video/webm"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Read file contents
    try:
        contents = await file.read()
        
        # Check file size (max 50MB for video)
        if len(contents) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Maximum size is 50MB."
            )
        
        # Run deepfake detection
        result = await analyze_image_for_deepfake(contents, content_type=file.content_type)
        
        # Save to history
        try:
            check = Check(
                user_id=current_user["user_id"],
                input_text=f"Media Analysis: {file.filename}",
                claim=f"Deepfake Analysis: {file.filename}",
                verdict=result["verdict"],
                confidence=result["confidence_level"],
                explanation="\n".join(result.get("evidence", []))[:4000] if result.get("evidence") else "No evidence provided",
                stance_summary=result, # Storing full result JSON including heatmap
                pipeline_version="deepfake-v1"
            )
            db.add(check)
            await db.commit()
        except Exception as e:
            print(f"Failed to save history: {e}")
            # Don't fail the request just because history save failed
            
        return MediaAnalysisResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )
