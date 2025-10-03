"""
Portfolio and position models for the trading platform.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Portfolio(Base):
    """Portfolio model representing user's investment portfolio."""
    
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Portfolio details
    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Financial metrics
    total_value = Column(Float, default=0.0)
    cash_balance = Column(Float, default=0.0)
    invested_value = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    total_pnl_percent = Column(Float, default=0.0)
    
    # Risk metrics
    beta = Column(Float, default=0.0)
    volatility = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_rebalance = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio")
    
    def __repr__(self):
        return f"<Portfolio(name='{self.name}', user_id={self.user_id}, total_value={self.total_value})>"
    
    def to_dict(self):
        """Convert portfolio to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "total_value": self.total_value,
            "cash_balance": self.cash_balance,
            "invested_value": self.invested_value,
            "total_pnl": self.total_pnl,
            "total_pnl_percent": self.total_pnl_percent,
            "beta": self.beta,
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_rebalance": self.last_rebalance.isoformat() if self.last_rebalance else None
        }


class Position(Base):
    """Position model representing holdings in a portfolio."""
    
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    
    # Position details
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    market_value = Column(Float, default=0.0)  # quantity * current_price
    
    # P&L tracking
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    pnl_percent = Column(Float, default=0.0)
    
    # Position metrics
    cost_basis = Column(Float, default=0.0)  # quantity * average_price
    weight_percent = Column(Float, default=0.0)  # Position weight in portfolio
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_price_update = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    asset = relationship("Asset", back_populates="positions")
    
    def __repr__(self):
        return f"<Position(asset_id={self.asset_id}, quantity={self.quantity}, avg_price={self.average_price})>"
    
    def to_dict(self):
        """Convert position to dictionary."""
        return {
            "id": self.id,
            "portfolio_id": self.portfolio_id,
            "asset_id": self.asset_id,
            "quantity": self.quantity,
            "average_price": self.average_price,
            "current_price": self.current_price,
            "market_value": self.market_value,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "total_pnl": self.total_pnl,
            "pnl_percent": self.pnl_percent,
            "cost_basis": self.cost_basis,
            "weight_percent": self.weight_percent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_price_update": self.last_price_update.isoformat() if self.last_price_update else None
        }
