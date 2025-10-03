"""
Trade-related API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.trade import Trade
from app.models.asset import Asset
from shared.enums.asset_types import OrderSide, OrderType

router = APIRouter()


class TradeCreate(BaseModel):
    """Schema for creating a new trade."""
    asset_id: int
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: Optional[str] = None


@router.get("/", response_model=List[dict])
async def get_trades(
    user_id: int = Query(..., description="User ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get user's trades."""
    trades = db.query(Trade).filter(
        Trade.user_id == user_id
    ).offset(offset).limit(limit).all()
    
    return [trade.to_dict() for trade in trades]


@router.post("/", response_model=dict)
async def create_trade(
    trade_data: TradeCreate,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Create a new trade."""
    # Verify asset exists
    asset = db.query(Asset).filter(Asset.id == trade_data.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Calculate total value
    if trade_data.price is None:
        if asset.current_price is None:
            raise HTTPException(status_code=400, detail="Asset price not available")
        price = asset.current_price
    else:
        price = trade_data.price
    
    total_value = trade_data.quantity * price
    
    # Create trade
    trade = Trade(
        user_id=user_id,
        asset_id=trade_data.asset_id,
        symbol=asset.symbol,
        side=trade_data.side,
        order_type=trade_data.order_type,
        quantity=trade_data.quantity,
        price=price,
        total_value=total_value,
        stop_loss=trade_data.stop_loss,
        take_profit=trade_data.take_profit,
        notes=trade_data.notes
    )
    
    db.add(trade)
    db.commit()
    db.refresh(trade)
    
    return trade.to_dict()


@router.get("/{trade_id}", response_model=dict)
async def get_trade(trade_id: int, db: Session = Depends(get_db)):
    """Get a specific trade."""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade.to_dict()


@router.put("/{trade_id}/cancel", response_model=dict)
async def cancel_trade(trade_id: int, db: Session = Depends(get_db)):
    """Cancel a trade."""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade.status.value in ["FILLED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="Trade cannot be cancelled")
    
    trade.status = "CANCELLED"
    db.commit()
    db.refresh(trade)
    
    return trade.to_dict()
