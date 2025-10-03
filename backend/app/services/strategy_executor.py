"""
Strategy execution service for algorithmic trading.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np

from app.database import get_db
from app.models.strategy import Strategy, AlgoStrategy
from app.models.trade import Trade, OrderSide, OrderType, OrderStatus
from app.models.asset import Asset
from app.models.market_data import MarketData
from app.services.asset_handlers import AssetHandlerService
from shared.enums.asset_types import StrategyType


class StrategyExecutor:
    """Service for executing trading strategies."""
    
    def __init__(self):
        self.asset_handler = AssetHandlerService()
    
    async def execute_strategy(self, strategy_id: int, db: Session) -> Dict[str, Any]:
        """Execute a trading strategy."""
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        if not strategy.is_active:
            return {"status": "skipped", "reason": "Strategy is not active"}
        
        try:
            if strategy.type == StrategyType.TREND_FOLLOWING:
                return await self._execute_trend_following(strategy, db)
            elif strategy.type == StrategyType.MEAN_REVERSION:
                return await self._execute_mean_reversion(strategy, db)
            elif strategy.type == StrategyType.ML_PREDICTIVE:
                return await self._execute_ml_predictive(strategy, db)
            else:
                return {"status": "error", "reason": f"Strategy type {strategy.type} not implemented"}
        
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    async def _execute_trend_following(self, strategy: Strategy, db: Session) -> Dict[str, Any]:
        """Execute trend following strategy."""
        # Get strategy parameters
        params = strategy.parameters or {}
        short_window = params.get('short_window', 20)
        long_window = params.get('long_window', 50)
        rsi_threshold = params.get('rsi_threshold', 70)
        
        # Get user's assets
        user_assets = self._get_user_assets(strategy.user_id, db)
        trades_executed = []
        
        for asset in user_assets:
            # Get recent market data
            market_data = db.query(MarketData).filter(
                MarketData.asset_id == asset.id
            ).order_by(MarketData.timestamp.desc()).limit(long_window).all()
            
            if len(market_data) < long_window:
                continue
            
            # Calculate indicators
            prices = [md.price for md in reversed(market_data)]
            df = pd.DataFrame({'price': prices})
            
            # Calculate moving averages
            df['sma_short'] = df['price'].rolling(window=short_window).mean()
            df['sma_long'] = df['price'].rolling(window=long_window).mean()
            
            # Calculate RSI
            df['rsi'] = self._calculate_rsi(df['price'])
            
            if len(df) < 2:
                continue
            
            current_price = prices[-1]
            sma_short = df['sma_short'].iloc[-1]
            sma_long = df['sma_long'].iloc[-1]
            rsi = df['rsi'].iloc[-1]
            
            # Check for buy signal
            if (sma_short > sma_long and 
                rsi < rsi_threshold and 
                current_price > sma_short):
                
                trade = await self._create_trade(
                    strategy, asset, OrderSide.BUY, current_price, db
                )
                if trade:
                    trades_executed.append(trade)
            
            # Check for sell signal
            elif (sma_short < sma_long and 
                  rsi > (100 - rsi_threshold) and 
                  current_price < sma_short):
                
                trade = await self._create_trade(
                    strategy, asset, OrderSide.SELL, current_price, db
                )
                if trade:
                    trades_executed.append(trade)
        
        return {
            "status": "completed",
            "strategy_id": strategy.id,
            "trades_executed": len(trades_executed),
            "trades": [trade.to_dict() for trade in trades_executed]
        }
    
    async def _execute_mean_reversion(self, strategy: Strategy, db: Session) -> Dict[str, Any]:
        """Execute mean reversion strategy."""
        params = strategy.parameters or {}
        lookback_period = params.get('lookback_period', 20)
        z_score_threshold = params.get('z_score_threshold', 2.0)
        
        user_assets = self._get_user_assets(strategy.user_id, db)
        trades_executed = []
        
        for asset in user_assets:
            market_data = db.query(MarketData).filter(
                MarketData.asset_id == asset.id
            ).order_by(MarketData.timestamp.desc()).limit(lookback_period).all()
            
            if len(market_data) < lookback_period:
                continue
            
            prices = [md.price for md in reversed(market_data)]
            current_price = prices[-1]
            
            # Calculate z-score
            mean_price = np.mean(prices[:-1])  # Exclude current price
            std_price = np.std(prices[:-1])
            z_score = (current_price - mean_price) / std_price if std_price > 0 else 0
            
            # Check for mean reversion signals
            if z_score < -z_score_threshold:  # Oversold - buy signal
                trade = await self._create_trade(
                    strategy, asset, OrderSide.BUY, current_price, db
                )
                if trade:
                    trades_executed.append(trade)
            
            elif z_score > z_score_threshold:  # Overbought - sell signal
                trade = await self._create_trade(
                    strategy, asset, OrderSide.SELL, current_price, db
                )
                if trade:
                    trades_executed.append(trade)
        
        return {
            "status": "completed",
            "strategy_id": strategy.id,
            "trades_executed": len(trades_executed),
            "trades": [trade.to_dict() for trade in trades_executed]
        }
    
    async def _execute_ml_predictive(self, strategy: Strategy, db: Session) -> Dict[str, Any]:
        """Execute ML predictive strategy."""
        # Get the associated algo strategy
        algo_strategy = db.query(AlgoStrategy).filter(
            AlgoStrategy.strategy_id == strategy.id
        ).first()
        
        if not algo_strategy or not algo_strategy.is_trained:
            return {
                "status": "skipped",
                "reason": "ML model not trained or not available"
            }
        
        # This would integrate with the ML prediction service
        # For now, return a placeholder
        return {
            "status": "completed",
            "strategy_id": strategy.id,
            "trades_executed": 0,
            "message": "ML strategy execution placeholder"
        }
    
    def _get_user_assets(self, user_id: int, db: Session) -> List[Asset]:
        """Get assets that the user is interested in trading."""
        # This would typically get from user preferences or portfolio
        # For now, return all active assets
        return db.query(Asset).filter(Asset.is_active == True).limit(10).all()
    
    async def _create_trade(
        self, 
        strategy: Strategy, 
        asset: Asset, 
        side: OrderSide, 
        price: float, 
        db: Session
    ) -> Optional[Trade]:
        """Create a trade based on strategy signal."""
        # Calculate position size based on strategy parameters
        max_position_size = strategy.max_position_size
        quantity = max_position_size / price  # Simple position sizing
        
        # Check if user has sufficient balance (simplified)
        # In a real implementation, this would check actual portfolio balance
        
        trade = Trade(
            user_id=strategy.user_id,
            asset_id=asset.id,
            strategy_id=strategy.id,
            symbol=asset.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            price=price,
            total_value=quantity * price,
            status=OrderStatus.PENDING,
            is_paper_trade=True  # For now, all trades are paper trades
        )
        
        db.add(trade)
        db.commit()
        db.refresh(trade)
        
        return trade
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    async def backtest_strategy(
        self, 
        strategy_id: int, 
        start_date: datetime, 
        end_date: datetime, 
        db: Session
    ) -> Dict[str, Any]:
        """Backtest a strategy on historical data."""
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        # Get historical data for the period
        historical_data = db.query(MarketData).filter(
            MarketData.timestamp >= start_date,
            MarketData.timestamp <= end_date
        ).order_by(MarketData.timestamp).all()
        
        if not historical_data:
            return {"status": "error", "reason": "No historical data available"}
        
        # Simulate strategy execution
        trades = []
        portfolio_value = 10000  # Starting value
        cash = 10000
        positions = {}
        
        for data_point in historical_data:
            # This would contain the actual strategy logic
            # For now, return a simple backtest result
            pass
        
        return {
            "status": "completed",
            "strategy_id": strategy_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_trades": len(trades),
            "final_value": portfolio_value,
            "total_return": (portfolio_value - 10000) / 10000 * 100,
            "trades": trades
        }
