"""
Asset model for the trading platform.
"""

from sqlalchemy import Column, Integer, String, Enum, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base
from shared.enums.asset_types import AssetType


class Asset(Base):
    """Asset model representing financial instruments."""
    
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(Enum(AssetType), nullable=False, index=True)
    exchange = Column(String(50), nullable=True)
    currency = Column(String(3), default="USD")
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    
    # Price information
    current_price = Column(Float, nullable=True)
    previous_close = Column(Float, nullable=True)
    day_high = Column(Float, nullable=True)
    day_low = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_price_update = Column(DateTime(timezone=True), nullable=True)
    
    # Additional data (JSON field for flexible data storage)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    trades = relationship("Trade", back_populates="asset")
    positions = relationship("Position", back_populates="asset")
    market_data = relationship("MarketData", back_populates="asset")
    historical_data = relationship("HistoricalData", back_populates="asset")
    
    def __repr__(self):
        return f"<Asset(symbol='{self.symbol}', name='{self.name}', type='{self.type}')>"
    
    def to_dict(self):
        """Convert asset to dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "type": self.type.value,
            "exchange": self.exchange,
            "currency": self.currency,
            "sector": self.sector,
            "industry": self.industry,
            "current_price": self.current_price,
            "previous_close": self.previous_close,
            "day_high": self.day_high,
            "day_low": self.day_low,
            "volume": self.volume,
            "market_cap": self.market_cap,
            "description": self.description,
            "website": self.website,
            "logo_url": self.logo_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_price_update": self.last_price_update.isoformat() if self.last_price_update else None,
            "metadata": self.metadata
        }
