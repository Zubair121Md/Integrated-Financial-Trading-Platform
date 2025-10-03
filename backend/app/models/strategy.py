"""
Strategy models for the trading platform.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base
from shared.enums.asset_types import StrategyType, RiskLevel, MLTechnique


class Strategy(Base):
    """Base strategy model for trading strategies."""
    
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Strategy details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(StrategyType), nullable=False)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.MEDIUM)
    
    # Configuration
    is_active = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    is_paper_trading = Column(Boolean, default=True)
    
    # Performance metrics
    total_return = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    
    # Risk parameters
    max_position_size = Column(Float, default=5.0)  # Percentage of portfolio
    stop_loss_percent = Column(Float, default=2.0)
    take_profit_percent = Column(Float, default=5.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_run = Column(DateTime(timezone=True), nullable=True)
    
    # Additional configuration (JSON field)
    parameters = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="strategies")
    trades = relationship("Trade", back_populates="strategy")
    algo_strategies = relationship("AlgoStrategy", back_populates="strategy")
    
    def __repr__(self):
        return f"<Strategy(name='{self.name}', type='{self.type}', user_id={self.user_id})>"
    
    def to_dict(self):
        """Convert strategy to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "risk_level": self.risk_level.value,
            "is_active": self.is_active,
            "is_public": self.is_public,
            "is_paper_trading": self.is_paper_trading,
            "total_return": self.total_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "total_trades": self.total_trades,
            "max_position_size": self.max_position_size,
            "stop_loss_percent": self.stop_loss_percent,
            "take_profit_percent": self.take_profit_percent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "parameters": self.parameters
        }


class AlgoStrategy(Base):
    """Algorithmic trading strategy model with ML capabilities."""
    
    __tablename__ = "algo_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    
    # ML Configuration
    ml_technique = Column(Enum(MLTechnique), nullable=False)
    model_path = Column(String(500), nullable=True)  # S3 path to trained model
    model_version = Column(String(50), nullable=True)
    
    # Training data
    training_data_path = Column(String(500), nullable=True)
    training_period_days = Column(Integer, default=365)
    validation_period_days = Column(Integer, default=90)
    
    # Model performance
    accuracy = Column(Float, default=0.0)
    precision = Column(Float, default=0.0)
    recall = Column(Float, default=0.0)
    f1_score = Column(Float, default=0.0)
    
    # Execution parameters
    prediction_threshold = Column(Float, default=0.5)
    confidence_threshold = Column(Float, default=0.7)
    retrain_frequency_hours = Column(Integer, default=24)
    
    # Status
    is_trained = Column(Boolean, default=False)
    is_deployed = Column(Boolean, default=False)
    last_trained = Column(DateTime(timezone=True), nullable=True)
    last_prediction = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Model configuration (JSON field)
    model_config = Column(JSON, nullable=True)
    feature_importance = Column(JSON, nullable=True)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="algo_strategies")
    
    def __repr__(self):
        return f"<AlgoStrategy(strategy_id={self.strategy_id}, ml_technique='{self.ml_technique}')>"
    
    def to_dict(self):
        """Convert algo strategy to dictionary."""
        return {
            "id": self.id,
            "strategy_id": self.strategy_id,
            "ml_technique": self.ml_technique.value,
            "model_path": self.model_path,
            "model_version": self.model_version,
            "training_data_path": self.training_data_path,
            "training_period_days": self.training_period_days,
            "validation_period_days": self.validation_period_days,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "prediction_threshold": self.prediction_threshold,
            "confidence_threshold": self.confidence_threshold,
            "retrain_frequency_hours": self.retrain_frequency_hours,
            "is_trained": self.is_trained,
            "is_deployed": self.is_deployed,
            "last_trained": self.last_trained.isoformat() if self.last_trained else None,
            "last_prediction": self.last_prediction.isoformat() if self.last_prediction else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "model_config": self.model_config,
            "feature_importance": self.feature_importance
        }
