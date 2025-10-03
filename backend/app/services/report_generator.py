"""
Report generation service for performance analytics.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.trade import Trade
from app.models.user import User
from app.models.portfolio import Portfolio, Position
from app.models.market_data import MarketData


class ReportGenerator:
    """Service for generating performance reports and analytics."""
    
    def __init__(self):
        pass
    
    async def generate_performance_report(
        self, 
        user_id: int, 
        start_date: datetime, 
        end_date: datetime, 
        db: Session
    ) -> Dict[str, Any]:
        """Generate comprehensive performance report for a user."""
        
        # Get user trades in date range
        trades = db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.created_at >= start_date,
            Trade.created_at <= end_date
        ).all()
        
        if not trades:
            return {
                "user_id": user_id,
                "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
                "message": "No trades found for the specified period"
            }
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([trade.to_dict() for trade in trades])
        
        # Calculate basic metrics
        total_trades = len(trades)
        winning_trades = len(df[df['realized_pnl'] > 0])
        losing_trades = len(df[df['realized_pnl'] < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate P&L metrics
        total_pnl = df['realized_pnl'].sum()
        total_volume = df['total_value'].sum()
        avg_trade_pnl = df['realized_pnl'].mean()
        
        # Calculate risk metrics
        returns = df['realized_pnl'].values
        volatility = np.std(returns) if len(returns) > 1 else 0
        sharpe_ratio = (np.mean(returns) / volatility) if volatility > 0 else 0
        
        # Calculate drawdown
        cumulative_pnl = df['realized_pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = cumulative_pnl - running_max
        max_drawdown = drawdown.min()
        
        # Calculate additional metrics
        profit_factor = self._calculate_profit_factor(df)
        avg_win = df[df['realized_pnl'] > 0]['realized_pnl'].mean() if winning_trades > 0 else 0
        avg_loss = df[df['realized_pnl'] < 0]['realized_pnl'].mean() if losing_trades > 0 else 0
        
        # Asset performance breakdown
        asset_performance = self._calculate_asset_performance(df)
        
        # Monthly performance
        monthly_performance = self._calculate_monthly_performance(df, start_date, end_date)
        
        return {
            "user_id": user_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "summary": {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": round(win_rate, 2),
                "total_pnl": round(total_pnl, 2),
                "total_volume": round(total_volume, 2),
                "avg_trade_pnl": round(avg_trade_pnl, 2),
                "profit_factor": round(profit_factor, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2)
            },
            "risk_metrics": {
                "volatility": round(volatility, 2),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "max_drawdown": round(max_drawdown, 2),
                "max_drawdown_percent": round((max_drawdown / total_volume * 100), 2) if total_volume > 0 else 0
            },
            "asset_performance": asset_performance,
            "monthly_performance": monthly_performance
        }
    
    async def generate_portfolio_report(
        self, 
        user_id: int, 
        db: Session
    ) -> Dict[str, Any]:
        """Generate portfolio analysis report."""
        
        # Get user's portfolio
        portfolio = db.query(Portfolio).filter(
            Portfolio.user_id == user_id,
            Portfolio.is_active == True
        ).first()
        
        if not portfolio:
            return {"message": "No active portfolio found"}
        
        # Get positions
        positions = db.query(Position).filter(
            Position.portfolio_id == portfolio.id
        ).all()
        
        if not positions:
            return {
                "portfolio_id": portfolio.id,
                "message": "No positions found"
            }
        
        # Calculate portfolio metrics
        total_value = sum(pos.market_value for pos in positions)
        total_cost = sum(pos.cost_basis for pos in positions)
        total_pnl = sum(pos.unrealized_pnl for pos in positions)
        total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        # Asset allocation
        asset_allocation = []
        for pos in positions:
            weight = (pos.market_value / total_value * 100) if total_value > 0 else 0
            asset_allocation.append({
                "symbol": pos.asset.symbol,
                "name": pos.asset.name,
                "quantity": pos.quantity,
                "market_value": pos.market_value,
                "cost_basis": pos.cost_basis,
                "unrealized_pnl": pos.unrealized_pnl,
                "unrealized_pnl_percent": pos.pnl_percent,
                "weight_percent": round(weight, 2)
            })
        
        # Sort by weight
        asset_allocation.sort(key=lambda x: x['weight_percent'], reverse=True)
        
        return {
            "portfolio_id": portfolio.id,
            "portfolio_name": portfolio.name,
            "summary": {
                "total_value": round(total_value, 2),
                "total_cost": round(total_cost, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_percent": round(total_pnl_percent, 2),
                "cash_balance": portfolio.cash_balance,
                "invested_value": portfolio.invested_value,
                "num_positions": len(positions)
            },
            "asset_allocation": asset_allocation,
            "risk_metrics": {
                "beta": portfolio.beta,
                "volatility": portfolio.volatility,
                "sharpe_ratio": portfolio.sharpe_ratio,
                "max_drawdown": portfolio.max_drawdown
            }
        }
    
    async def generate_strategy_report(
        self, 
        strategy_id: int, 
        start_date: datetime, 
        end_date: datetime, 
        db: Session
    ) -> Dict[str, Any]:
        """Generate strategy performance report."""
        
        # Get strategy trades
        trades = db.query(Trade).filter(
            Trade.strategy_id == strategy_id,
            Trade.created_at >= start_date,
            Trade.created_at <= end_date
        ).all()
        
        if not trades:
            return {
                "strategy_id": strategy_id,
                "message": "No trades found for this strategy"
            }
        
        df = pd.DataFrame([trade.to_dict() for trade in trades])
        
        # Calculate strategy metrics
        total_trades = len(trades)
        winning_trades = len(df[df['realized_pnl'] > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = df['realized_pnl'].sum()
        avg_trade_pnl = df['realized_pnl'].mean()
        
        # Calculate returns
        returns = df['realized_pnl'].values
        volatility = np.std(returns) if len(returns) > 1 else 0
        sharpe_ratio = (np.mean(returns) / volatility) if volatility > 0 else 0
        
        # Calculate drawdown
        cumulative_pnl = df['realized_pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = cumulative_pnl - running_max
        max_drawdown = drawdown.min()
        
        return {
            "strategy_id": strategy_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "performance": {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "win_rate": round(win_rate, 2),
                "total_pnl": round(total_pnl, 2),
                "avg_trade_pnl": round(avg_trade_pnl, 2),
                "volatility": round(volatility, 2),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "max_drawdown": round(max_drawdown, 2)
            }
        }
    
    def _calculate_profit_factor(self, df: pd.DataFrame) -> float:
        """Calculate profit factor (gross profit / gross loss)."""
        gross_profit = df[df['realized_pnl'] > 0]['realized_pnl'].sum()
        gross_loss = abs(df[df['realized_pnl'] < 0]['realized_pnl'].sum())
        
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    def _calculate_asset_performance(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Calculate performance breakdown by asset."""
        asset_perf = df.groupby('symbol').agg({
            'realized_pnl': ['sum', 'count', 'mean'],
            'total_value': 'sum'
        }).round(2)
        
        asset_perf.columns = ['total_pnl', 'trade_count', 'avg_pnl', 'total_volume']
        asset_perf = asset_perf.reset_index()
        
        return asset_perf.to_dict('records')
    
    def _calculate_monthly_performance(
        self, 
        df: pd.DataFrame, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Calculate monthly performance breakdown."""
        df['month'] = pd.to_datetime(df['created_at']).dt.to_period('M')
        monthly_perf = df.groupby('month').agg({
            'realized_pnl': ['sum', 'count'],
            'total_value': 'sum'
        }).round(2)
        
        monthly_perf.columns = ['pnl', 'trade_count', 'volume']
        monthly_perf = monthly_perf.reset_index()
        monthly_perf['month'] = monthly_perf['month'].astype(str)
        
        return monthly_perf.to_dict('records')
    
    async def generate_risk_report(
        self, 
        user_id: int, 
        db: Session
    ) -> Dict[str, Any]:
        """Generate risk analysis report."""
        
        # Get recent trades for risk analysis
        recent_trades = db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.created_at >= datetime.now() - timedelta(days=30)
        ).all()
        
        if not recent_trades:
            return {"message": "No recent trades for risk analysis"}
        
        df = pd.DataFrame([trade.to_dict() for trade in recent_trades])
        
        # Calculate VaR (Value at Risk)
        returns = df['realized_pnl'].values
        var_95 = np.percentile(returns, 5)  # 95% VaR
        var_99 = np.percentile(returns, 1)  # 99% VaR
        
        # Calculate position concentration
        position_sizes = df['total_value'].values
        max_position = np.max(position_sizes)
        avg_position = np.mean(position_sizes)
        concentration_risk = max_position / np.sum(position_sizes) if np.sum(position_sizes) > 0 else 0
        
        # Calculate correlation risk (simplified)
        daily_returns = df.groupby(pd.to_datetime(df['created_at']).dt.date)['realized_pnl'].sum()
        volatility = daily_returns.std()
        
        return {
            "user_id": user_id,
            "risk_metrics": {
                "var_95": round(var_95, 2),
                "var_99": round(var_99, 2),
                "max_position_size": round(max_position, 2),
                "avg_position_size": round(avg_position, 2),
                "concentration_risk": round(concentration_risk * 100, 2),
                "daily_volatility": round(volatility, 2)
            },
            "recommendations": self._generate_risk_recommendations(
                var_95, concentration_risk, volatility
            )
        }
    
    def _generate_risk_recommendations(
        self, 
        var_95: float, 
        concentration_risk: float, 
        volatility: float
    ) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []
        
        if var_95 < -1000:
            recommendations.append("Consider reducing position sizes to limit downside risk")
        
        if concentration_risk > 0.3:
            recommendations.append("Portfolio is too concentrated. Consider diversifying across more assets")
        
        if volatility > 500:
            recommendations.append("High volatility detected. Consider implementing stop-loss orders")
        
        if not recommendations:
            recommendations.append("Risk profile appears balanced")
        
        return recommendations
