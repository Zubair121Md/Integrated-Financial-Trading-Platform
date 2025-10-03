"""
User model for the trading platform.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User model for authentication and user management."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    
    # Trading preferences
    risk_tolerance = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH
    trading_experience = Column(String(20), default="BEGINNER")  # BEGINNER, INTERMEDIATE, ADVANCED
    preferred_asset_types = Column(Text, nullable=True)  # JSON string of asset types
    
    # Financial information
    initial_balance = Column(Float, default=10000.0)  # Starting balance for paper trading
    current_balance = Column(Float, default=10000.0)
    total_pnl = Column(Float, default=0.0)
    
    # Subscription information
    subscription_tier = Column(String(20), default="FREE")  # FREE, BASIC, PREMIUM, PRO
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Profile information
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default="UTC")
    
    # Relationships
    trades = relationship("Trade", back_populates="user")
    portfolios = relationship("Portfolio", back_populates="user")
    strategies = relationship("Strategy", back_populates="user")
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
    
    def to_dict(self):
        """Convert user to dictionary (excluding sensitive data)."""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_premium": self.is_premium,
            "risk_tolerance": self.risk_tolerance,
            "trading_experience": self.trading_experience,
            "preferred_asset_types": self.preferred_asset_types,
            "initial_balance": self.initial_balance,
            "current_balance": self.current_balance,
            "total_pnl": self.total_pnl,
            "subscription_tier": self.subscription_tier,
            "subscription_expires_at": self.subscription_expires_at.isoformat() if self.subscription_expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "timezone": self.timezone
        }
