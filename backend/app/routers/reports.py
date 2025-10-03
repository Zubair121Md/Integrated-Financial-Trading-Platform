"""
Reporting and analytics API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.models.trade import Trade
from app.models.user import User
from app.services.report_generator import ReportGenerator
from app.services.backtester import Backtester

router = APIRouter()


@router.get("/performance/{user_id}")
async def get_performance_report(
    user_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get performance report for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate date range
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Get trades in date range
    trades = db.query(Trade).filter(
        Trade.user_id == user_id,
        Trade.created_at >= start_date,
        Trade.created_at <= end_date
    ).all()
    
    # Calculate metrics
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t.realized_pnl > 0])
    losing_trades = len([t for t in trades if t.realized_pnl < 0])
    
    total_pnl = sum(t.realized_pnl for t in trades)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    avg_win = sum(t.realized_pnl for t in trades if t.realized_pnl > 0) / max(winning_trades, 1)
    avg_loss = sum(t.realized_pnl for t in trades if t.realized_pnl < 0) / max(losing_trades, 1)
    
    return {
        "user_id": user_id,
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "summary": {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0
        },
        "portfolio": {
            "current_balance": user.current_balance,
            "total_pnl": user.total_pnl,
            "total_pnl_percent": round((user.total_pnl / user.initial_balance * 100), 2) if user.initial_balance > 0 else 0
        }
    }


@router.get("/trades/{user_id}")
async def get_trade_report(
    user_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get detailed trade report for a user."""
    trades = db.query(Trade).filter(
        Trade.user_id == user_id
    ).offset(offset).limit(limit).all()
    
    return {
        "user_id": user_id,
        "trades": [trade.to_dict() for trade in trades],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": db.query(Trade).filter(Trade.user_id == user_id).count()
        }
    }


@router.get("/portfolio/{user_id}")
async def get_portfolio_report(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get portfolio report for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get recent trades for analysis
    recent_trades = db.query(Trade).filter(
        Trade.user_id == user_id,
        Trade.created_at >= datetime.now() - timedelta(days=7)
    ).all()
    
    # Calculate weekly performance
    weekly_pnl = sum(t.realized_pnl for t in recent_trades)
    
    return {
        "user_id": user_id,
        "portfolio_summary": {
            "initial_balance": user.initial_balance,
            "current_balance": user.current_balance,
            "total_pnl": user.total_pnl,
            "total_pnl_percent": round((user.total_pnl / user.initial_balance * 100), 2) if user.initial_balance > 0 else 0,
            "weekly_pnl": round(weekly_pnl, 2)
        },
        "account_info": {
            "subscription_tier": user.subscription_tier,
            "risk_tolerance": user.risk_tolerance,
            "trading_experience": user.trading_experience,
            "member_since": user.created_at.isoformat() if user.created_at else None
        }
    }


@router.get("/portfolio/{user_id}")
async def get_portfolio_report(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get portfolio analysis report for a user."""
    report_generator = ReportGenerator()
    report = await report_generator.generate_portfolio_report(user_id, db)
    return report


@router.get("/strategy/{strategy_id}")
async def get_strategy_report(
    strategy_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get strategy performance report."""
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    
    report_generator = ReportGenerator()
    report = await report_generator.generate_strategy_report(
        strategy_id, start_dt, end_dt, db
    )
    return report


@router.get("/risk/{user_id}")
async def get_risk_report(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get risk analysis report for a user."""
    report_generator = ReportGenerator()
    report = await report_generator.generate_risk_report(user_id, db)
    return report


@router.post("/backtest/{strategy_id}")
async def backtest_strategy(
    strategy_id: int,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    initial_capital: float = Query(10000.0, description="Initial capital for backtesting"),
    db: Session = Depends(get_db)
):
    """Backtest a strategy on historical data."""
    from app.models.strategy import Strategy
    
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    
    backtester = Backtester()
    result = await backtester.backtest_strategy(
        strategy, start_dt, end_dt, initial_capital, db
    )
    
    return result
