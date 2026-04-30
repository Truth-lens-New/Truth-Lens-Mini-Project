"""
TruthLens History API v1

API endpoints for managing user's analysis history.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.check import Check


router = APIRouter(prefix="/api/v1/history", tags=["History"])


# Response Schemas
class HistoryItemResponse(BaseModel):
    """Single history item."""
    id: int
    claim: Optional[str]
    verdict: str
    confidence: str
    explanation: Optional[str]
    claim_type: Optional[str]
    metadata: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True


class HistoryDetailResponse(BaseModel):
    """Detailed history item response."""
    id: int
    claim: Optional[str]
    input_text: Optional[str]
    input_url: Optional[str]
    verdict: str
    confidence: str
    explanation: Optional[str]
    domain_score: Optional[str]
    factcheck_rating: Optional[str]
    factcheck_summary: Optional[str]
    stance_summary: Optional[dict]
    claim_type: Optional[str]
    metadata: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True


class HistoryListResponse(BaseModel):
    """History list response."""
    items: List[HistoryItemResponse]
    total: int


@router.get("", response_model=HistoryListResponse)
async def get_history(
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's analysis history.
    
    Args:
        skip: Number of items to skip (pagination)
        limit: Maximum items to return
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of history items
    """
    user_id = current_user['user_id']
    
    # Get total count
    count_query = select(Check).where(Check.user_id == user_id)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    # Get paginated items
    query = (
        select(Check)
        .where(Check.user_id == user_id)
        .order_by(Check.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return HistoryListResponse(
        items=[
            HistoryItemResponse(
                id=item.id,
                claim=item.claim,
                verdict=item.verdict,
                confidence=item.confidence,
                explanation=item.explanation,
                claim_type=item.claim_type,
                metadata=item.extra_metadata,
                created_at=item.created_at
            )
            for item in items
        ],
        total=total
    )


@router.get("/{check_id}", response_model=HistoryDetailResponse)
async def get_history_item(
    check_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific analysis result.
    
    Args:
        check_id: ID of the check to retrieve
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Detailed analysis result
    """
    user_id = current_user['user_id']
    
    query = select(Check).where(Check.id == check_id, Check.user_id == user_id)
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return HistoryDetailResponse(
        id=item.id,
        claim=item.claim,
        input_text=item.input_text,
        input_url=item.input_url,
        verdict=item.verdict,
        confidence=item.confidence,
        explanation=item.explanation,
        domain_score=item.domain_score,
        factcheck_rating=item.factcheck_rating,
        factcheck_summary=item.factcheck_summary,
        stance_summary=item.stance_summary,
        claim_type=item.claim_type,
        extra_metadata=item.extra_metadata,
        created_at=item.created_at
    )


@router.delete("/{check_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history_item(
    check_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a specific analysis result.
    
    Args:
        check_id: ID of the check to delete
        current_user: Authenticated user
        db: Database session
    """
    user_id = current_user['user_id']
    
    # Check if exists and belongs to user
    query = select(Check).where(Check.id == check_id, Check.user_id == user_id)
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    await db.delete(item)
    await db.commit()
    
    return None


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Clear all user's analysis history.
    
    Args:
        current_user: Authenticated user
        db: Database session
    """
    user_id = current_user['user_id']
    
    # Delete all user's checks
    stmt = delete(Check).where(Check.user_id == user_id)
    await db.execute(stmt)
    await db.commit()
    
    return None
