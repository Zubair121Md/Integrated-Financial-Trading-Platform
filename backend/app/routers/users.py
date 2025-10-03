"""
User-related API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models.user import User

router = APIRouter()


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    full_name: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = None
    risk_tolerance: Optional[str] = None
    trading_experience: Optional[str] = None


@router.get("/", response_model=List[dict])
async def get_users(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get list of users (admin only in production)."""
    users = db.query(User).offset(offset).limit(limit).all()
    return [user.to_dict() for user in users]


@router.get("/{user_id}", response_model=dict)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()


@router.post("/", response_model=dict)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user (password should be hashed in production)
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=user_data.password,  # Should hash this
        full_name=user_data.full_name
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user.to_dict()


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """Update user information."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.bio is not None:
        user.bio = user_data.bio
    if user_data.timezone is not None:
        user.timezone = user_data.timezone
    if user_data.risk_tolerance is not None:
        user.risk_tolerance = user_data.risk_tolerance
    if user_data.trading_experience is not None:
        user.trading_experience = user_data.trading_experience
    
    db.commit()
    db.refresh(user)
    
    return user.to_dict()


@router.get("/{user_id}/portfolio", response_model=dict)
async def get_user_portfolio(user_id: int, db: Session = Depends(get_db)):
    """Get user's portfolio summary."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": user_id,
        "current_balance": user.current_balance,
        "total_pnl": user.total_pnl,
        "total_pnl_percent": (user.total_pnl / user.initial_balance * 100) if user.initial_balance > 0 else 0,
        "subscription_tier": user.subscription_tier,
        "risk_tolerance": user.risk_tolerance,
        "trading_experience": user.trading_experience
    }
