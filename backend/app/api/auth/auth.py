"""
TruthLens Authentication API

Provides user registration and login endpoints.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.models.user import User
from app.models.check import Check


router = APIRouter(prefix="/auth", tags=["Authentication"])


# Request/Response Schemas
class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User data response."""
    id: int
    email: str
    
    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    """User profile update request."""
    full_name: str | None = None
    avatar_url: str | None = None
    preferences: dict | None = None
    password: str | None = None  # To change password if needed


class ProfileResponse(BaseModel):
    """User profile response with stats."""
    id: int
    email: str
    full_name: str | None = None
    avatar_url: str | None = None
    preferences: dict | None = None
    member_since: datetime
    total_analyses: int


@router.get("/me", response_model=ProfileResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's profile with stats.
    
    Returns:
        User profile with email, member_since date, and total analyses count
    """
    user_id = current_user['user_id']
    
    # Get user data
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Count total analyses
    count_result = await db.execute(
        select(func.count()).select_from(Check).where(Check.user_id == user_id)
    )
    total_analyses = count_result.scalar() or 0
    
    return ProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        preferences=user.preferences or {},
        member_since=user.created_at,
        total_analyses=total_analyses
    )



@router.patch("/me", response_model=ProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile.
    """
    user_id = current_user['user_id']
    
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Update fields
    if request.full_name is not None:
        user.full_name = request.full_name
    
    if request.avatar_url is not None:
        user.avatar_url = request.avatar_url
        
    if request.preferences is not None:
        # Merge existing preferences with new ones
        current_prefs = dict(user.preferences) if user.preferences else {}
        current_prefs.update(request.preferences)
        user.preferences = current_prefs
        
    if request.password:
        user.hashed_password = hash_password(request.password)
        
    await db.commit()
    await db.refresh(user)
    
    # Get stats for response
    count_result = await db.execute(
        select(func.count()).select_from(Check).where(Check.user_id == user_id)
    )
    total_analyses = count_result.scalar() or 0
    
    return ProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        preferences=user.preferences or {},
        member_since=user.created_at,
        total_analyses=total_analyses
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    Args:
        request: Registration data with email and password
        db: Database session
        
    Returns:
        Created user data
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_pwd = hash_password(request.password)
    user = User(
        email=request.email,
        hashed_password=hashed_pwd
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login and receive JWT token.
    
    Args:
        request: Login credentials
        db: Database session
        
    Returns:
        JWT access token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return TokenResponse(access_token=access_token)
