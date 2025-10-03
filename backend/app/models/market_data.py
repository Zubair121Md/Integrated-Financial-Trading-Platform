"""
Market data models for the trading platform.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class MarketData(Base):
    """Real-time market data model."""
    
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    
    # Price data
    symbol = Column(String(20), nullable=False, index=True)
    price = Column(Float, nullable=False)
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    previous_close = Column(Float, nullable=True)
    
    # Volume and market data
    volume = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)
    change = Column(Float, nullable=True)
    change_percent = Column(Float, nullable=True)
    
    # Technical indicators (cached for performance)
    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    sma_20 = Column(Float, nullable=True)
    sma_50 = Column(Float, nullable=True)
    ema_12 = Column(Float, nullable=True)
    ema_26 = Column(Float, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional data (JSON field for flexible data storage)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    asset = relationship("Asset", back_populates="market_data")
    
    def __repr__(self):
        return f"<MarketData(symbol='{self.symbol}', price={self.price}, timestamp='{self.timestamp}')>"
    
    def to_dict(self):
        """Convert market data to dictionary."""
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "symbol": self.symbol,
            "price": self.price,
            "open_price": self.open_price,
            "high_price": self.high_price,
            "low_price": self.low_price,
            "previous_close": self.previous_close,
            "volume": self.volume,
            "market_cap": self.market_cap,
            "change": self.change,
            "change_percent": self.change_percent,
            "rsi": self.rsi,
            "macd": self.macd,
            "sma_20": self.sma_20,
            "sma_50": self.sma_50,
            "ema_12": self.ema_12,
            "ema_26": self.ema_26,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata
        }


class HistoricalData(Base):
    """Historical market data model for backtesting and analysis."""
    
    __tablename__ = "historical_data"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    
    # OHLCV data
    symbol = Column(String(20), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    adjusted_close = Column(Float, nullable=True)
    
    # Additional price data
    vwap = Column(Float, nullable=True)  # Volume Weighted Average Price
    typical_price = Column(Float, nullable=True)  # (High + Low + Close) / 3
    weighted_close = Column(Float, nullable=True)  # (High + Low + 2*Close) / 4
    
    # Technical indicators
    sma_5 = Column(Float, nullable=True)
    sma_10 = Column(Float, nullable=True)
    sma_20 = Column(Float, nullable=True)
    sma_50 = Column(Float, nullable=True)
    sma_200 = Column(Float, nullable=True)
    
    ema_12 = Column(Float, nullable=True)
    ema_26 = Column(Float, nullable=True)
    
    rsi_14 = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_histogram = Column(Float, nullable=True)
    
    bollinger_upper = Column(Float, nullable=True)
    bollinger_middle = Column(Float, nullable=True)
    bollinger_lower = Column(Float, nullable=True)
    
    # Volatility indicators
    atr = Column(Float, nullable=True)  # Average True Range
    volatility = Column(Float, nullable=True)  # Historical volatility
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Additional data (JSON field for flexible data storage)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    asset = relationship("Asset", back_populates="historical_data")
    
    def __repr__(self):
        return f"<HistoricalData(symbol='{self.symbol}', date='{self.date}', close={self.close_price})>"
    
    def to_dict(self):
        """Convert historical data to dictionary."""
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "symbol": self.symbol,
            "date": self.date.isoformat() if self.date else None,
            "open_price": self.open_price,
            "high_price": self.high_price,
            "low_price": self.low_price,
            "close_price": self.close_price,
            "volume": self.volume,
            "adjusted_close": self.adjusted_close,
            "vwap": self.vwap,
            "typical_price": self.typical_price,
            "weighted_close": self.weighted_close,
            "sma_5": self.sma_5,
            "sma_10": self.sma_10,
            "sma_20": self.sma_20,
            "sma_50": self.sma_50,
            "sma_200": self.sma_200,
            "ema_12": self.ema_12,
            "ema_26": self.ema_26,
            "rsi_14": self.rsi_14,
            "macd": self.macd,
            "macd_signal": self.macd_signal,
            "macd_histogram": self.macd_histogram,
            "bollinger_upper": self.bollinger_upper,
            "bollinger_middle": self.bollinger_middle,
            "bollinger_lower": self.bollinger_lower,
            "atr": self.atr,
            "volatility": self.volatility,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata
        }
