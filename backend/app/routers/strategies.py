"""
Strategy-related API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.strategy import Strategy, AlgoStrategy
from shared.enums.asset_types import StrategyType, RiskLevel, MLTechnique

router = APIRouter()


class StrategyCreate(BaseModel):
    """Schema for creating a new strategy."""
    name: str
    description: Optional[str] = None
    type: StrategyType
    risk_level: RiskLevel = RiskLevel.MEDIUM
    max_position_size: float = 5.0
    stop_loss_percent: float = 2.0
    take_profit_percent: float = 5.0
    parameters: Optional[dict] = None


class AlgoStrategyCreate(BaseModel):
    """Schema for creating an algorithmic strategy."""
    strategy_id: int
    ml_technique: MLTechnique
    prediction_threshold: float = 0.5
    confidence_threshold: float = 0.7
    retrain_frequency_hours: int = 24
    model_config: Optional[dict] = None


@router.get("/", response_model=List[dict])
async def get_strategies(
    user_id: int = Query(..., description="User ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get user's strategies."""
    strategies = db.query(Strategy).filter(
        Strategy.user_id == user_id
    ).offset(offset).limit(limit).all()
    
    return [strategy.to_dict() for strategy in strategies]


@router.post("/", response_model=dict)
async def create_strategy(
    strategy_data: StrategyCreate,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Create a new strategy."""
    strategy = Strategy(
        user_id=user_id,
        name=strategy_data.name,
        description=strategy_data.description,
        type=strategy_data.type,
        risk_level=strategy_data.risk_level,
        max_position_size=strategy_data.max_position_size,
        stop_loss_percent=strategy_data.stop_loss_percent,
        take_profit_percent=strategy_data.take_profit_percent,
        parameters=strategy_data.parameters
    )
    
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    
    return strategy.to_dict()


@router.get("/{strategy_id}", response_model=dict)
async def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Get a specific strategy."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy.to_dict()


@router.put("/{strategy_id}/activate", response_model=dict)
async def activate_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Activate a strategy."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    strategy.is_active = True
    db.commit()
    db.refresh(strategy)
    
    return strategy.to_dict()


@router.put("/{strategy_id}/deactivate", response_model=dict)
async def deactivate_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Deactivate a strategy."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    strategy.is_active = False
    db.commit()
    db.refresh(strategy)
    
    return strategy.to_dict()


# Algo Strategy endpoints
@router.post("/algo", response_model=dict)
async def create_algo_strategy(
    algo_data: AlgoStrategyCreate,
    db: Session = Depends(get_db)
):
    """Create an algorithmic strategy."""
    # Verify parent strategy exists
    strategy = db.query(Strategy).filter(Strategy.id == algo_data.strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Parent strategy not found")
    
    algo_strategy = AlgoStrategy(
        strategy_id=algo_data.strategy_id,
        ml_technique=algo_data.ml_technique,
        prediction_threshold=algo_data.prediction_threshold,
        confidence_threshold=algo_data.confidence_threshold,
        retrain_frequency_hours=algo_data.retrain_frequency_hours,
        model_config=algo_data.model_config
    )
    
    db.add(algo_strategy)
    db.commit()
    db.refresh(algo_strategy)
    
    return algo_strategy.to_dict()


@router.get("/algo/{algo_strategy_id}", response_model=dict)
async def get_algo_strategy(algo_strategy_id: int, db: Session = Depends(get_db)):
    """Get a specific algorithmic strategy."""
    algo_strategy = db.query(AlgoStrategy).filter(AlgoStrategy.id == algo_strategy_id).first()
    if not algo_strategy:
        raise HTTPException(status_code=404, detail="Algorithmic strategy not found")
    return algo_strategy.to_dict()
