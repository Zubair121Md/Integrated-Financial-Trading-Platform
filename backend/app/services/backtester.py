"""
Backtesting service for strategy validation.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.models.market_data import MarketData
from app.models.asset import Asset
from shared.enums.asset_types import OrderSide, OrderType


class Backtester:
    """Service for backtesting trading strategies."""
    
    def __init__(self):
        self.initial_capital = 10000.0
        self.commission_rate = 0.001  # 0.1% commission
    
    async def backtest_strategy(
        self,
        strategy: Strategy,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000.0,
        db: Session = None
    ) -> Dict[str, Any]:
        """Backtest a strategy on historical data."""
        
        self.initial_capital = initial_capital
        
        # Get historical data for the period
        historical_data = self._get_historical_data(
            strategy, start_date, end_date, db
        )
        
        if historical_data.empty:
            return {
                "status": "error",
                "message": "No historical data available for backtesting"
            }
        
        # Initialize portfolio
        portfolio = {
            "cash": initial_capital,
            "positions": {},
            "trades": [],
            "equity_curve": []
        }
        
        # Execute strategy
        if strategy.type.value == "TREND_FOLLOWING":
            portfolio = await self._backtest_trend_following(
                strategy, historical_data, portfolio
            )
        elif strategy.type.value == "MEAN_REVERSION":
            portfolio = await self._backtest_mean_reversion(
                strategy, historical_data, portfolio
            )
        else:
            return {
                "status": "error",
                "message": f"Strategy type {strategy.type} not supported for backtesting"
            }
        
        # Calculate performance metrics
        performance = self._calculate_performance_metrics(portfolio)
        
        return {
            "status": "success",
            "strategy_id": strategy.id,
            "strategy_name": strategy.name,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "performance": performance,
            "trades": portfolio["trades"][-10:],  # Last 10 trades
            "equity_curve": portfolio["equity_curve"][-50:]  # Last 50 data points
        }
    
    def _get_historical_data(
        self,
        strategy: Strategy,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> pd.DataFrame:
        """Get historical market data for backtesting."""
        
        # Get all active assets (simplified - in real implementation, 
        # this would be based on strategy configuration)
        assets = db.query(Asset).filter(Asset.is_active == True).limit(5).all()
        
        if not assets:
            return pd.DataFrame()
        
        # Get market data for all assets
        all_data = []
        for asset in assets:
            market_data = db.query(MarketData).filter(
                MarketData.asset_id == asset.id,
                MarketData.timestamp >= start_date,
                MarketData.timestamp <= end_date
            ).order_by(MarketData.timestamp).all()
            
            for data in market_data:
                all_data.append({
                    "timestamp": data.timestamp,
                    "symbol": data.symbol,
                    "price": data.price,
                    "open": data.open_price or data.price,
                    "high": data.high_price or data.price,
                    "low": data.low_price or data.price,
                    "volume": data.volume or 0,
                    "asset_id": data.asset_id
                })
        
        df = pd.DataFrame(all_data)
        if df.empty:
            return df
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        return df
    
    async def _backtest_trend_following(
        self,
        strategy: Strategy,
        data: pd.DataFrame,
        portfolio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Backtest trend following strategy."""
        
        params = strategy.parameters or {}
        short_window = params.get('short_window', 20)
        long_window = params.get('long_window', 50)
        rsi_threshold = params.get('rsi_threshold', 70)
        
        # Group by symbol for individual asset analysis
        for symbol, asset_data in data.groupby('symbol'):
            asset_data = asset_data.sort_values('timestamp')
            
            # Calculate indicators
            asset_data['sma_short'] = asset_data['price'].rolling(window=short_window).mean()
            asset_data['sma_long'] = asset_data['price'].rolling(window=long_window).mean()
            asset_data['rsi'] = self._calculate_rsi(asset_data['price'])
            
            # Generate signals
            for i in range(long_window, len(asset_data)):
                current_data = asset_data.iloc[i]
                prev_data = asset_data.iloc[i-1]
                
                # Skip if indicators not available
                if pd.isna(current_data['sma_short']) or pd.isna(current_data['sma_long']):
                    continue
                
                # Check for buy signal
                if (current_data['sma_short'] > current_data['sma_long'] and
                    prev_data['sma_short'] <= prev_data['sma_long'] and
                    current_data['rsi'] < rsi_threshold):
                    
                    self._execute_trade(
                        portfolio, symbol, OrderSide.BUY, 
                        current_data['price'], current_data['timestamp']
                    )
                
                # Check for sell signal
                elif (current_data['sma_short'] < current_data['sma_long'] and
                      prev_data['sma_short'] >= prev_data['sma_long'] and
                      current_data['rsi'] > (100 - rsi_threshold)):
                    
                    self._execute_trade(
                        portfolio, symbol, OrderSide.SELL,
                        current_data['price'], current_data['timestamp']
                    )
                
                # Update equity curve
                self._update_equity_curve(portfolio, current_data['timestamp'])
        
        return portfolio
    
    async def _backtest_mean_reversion(
        self,
        strategy: Strategy,
        data: pd.DataFrame,
        portfolio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Backtest mean reversion strategy."""
        
        params = strategy.parameters or {}
        lookback_period = params.get('lookback_period', 20)
        z_score_threshold = params.get('z_score_threshold', 2.0)
        
        for symbol, asset_data in data.groupby('symbol'):
            asset_data = asset_data.sort_values('timestamp')
            
            for i in range(lookback_period, len(asset_data)):
                current_data = asset_data.iloc[i]
                lookback_data = asset_data.iloc[i-lookback_period:i]
                
                # Calculate z-score
                mean_price = lookback_data['price'].mean()
                std_price = lookback_data['price'].std()
                
                if std_price == 0:
                    continue
                
                z_score = (current_data['price'] - mean_price) / std_price
                
                # Check for mean reversion signals
                if z_score < -z_score_threshold:  # Oversold - buy signal
                    self._execute_trade(
                        portfolio, symbol, OrderSide.BUY,
                        current_data['price'], current_data['timestamp']
                    )
                elif z_score > z_score_threshold:  # Overbought - sell signal
                    self._execute_trade(
                        portfolio, symbol, OrderSide.SELL,
                        current_data['price'], current_data['timestamp']
                    )
                
                self._update_equity_curve(portfolio, current_data['timestamp'])
        
        return portfolio
    
    def _execute_trade(
        self,
        portfolio: Dict[str, Any],
        symbol: str,
        side: OrderSide,
        price: float,
        timestamp: datetime
    ) -> None:
        """Execute a trade in the backtest."""
        
        # Calculate position size (simplified)
        position_size = portfolio["cash"] * 0.1 / price  # 10% of cash per trade
        
        if side == OrderSide.BUY and portfolio["cash"] >= position_size * price:
            # Buy
            cost = position_size * price
            commission = cost * self.commission_rate
            total_cost = cost + commission
            
            if portfolio["cash"] >= total_cost:
                portfolio["cash"] -= total_cost
                portfolio["positions"][symbol] = portfolio["positions"].get(symbol, 0) + position_size
                
                portfolio["trades"].append({
                    "timestamp": timestamp.isoformat(),
                    "symbol": symbol,
                    "side": side.value,
                    "quantity": position_size,
                    "price": price,
                    "cost": total_cost,
                    "commission": commission
                })
        
        elif side == OrderSide.SELL and symbol in portfolio["positions"]:
            # Sell
            quantity = portfolio["positions"][symbol]
            proceeds = quantity * price
            commission = proceeds * self.commission_rate
            net_proceeds = proceeds - commission
            
            portfolio["cash"] += net_proceeds
            del portfolio["positions"][symbol]
            
            portfolio["trades"].append({
                "timestamp": timestamp.isoformat(),
                "symbol": symbol,
                "side": side.value,
                "quantity": quantity,
                "price": price,
                "proceeds": net_proceeds,
                "commission": commission
            })
    
    def _update_equity_curve(self, portfolio: Dict[str, Any], timestamp: datetime) -> None:
        """Update the equity curve."""
        total_value = portfolio["cash"]
        
        # Add position values (simplified - would need current prices)
        for symbol, quantity in portfolio["positions"].items():
            # In a real implementation, we'd get the current price
            # For now, use the last trade price
            if portfolio["trades"]:
                last_trade = portfolio["trades"][-1]
                if last_trade["symbol"] == symbol:
                    total_value += quantity * last_trade["price"]
        
        portfolio["equity_curve"].append({
            "timestamp": timestamp.isoformat(),
            "total_value": total_value,
            "cash": portfolio["cash"],
            "positions_value": total_value - portfolio["cash"]
        })
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_performance_metrics(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics from backtest results."""
        
        if not portfolio["equity_curve"]:
            return {}
        
        equity_df = pd.DataFrame(portfolio["equity_curve"])
        equity_df['timestamp'] = pd.to_datetime(equity_df['timestamp'])
        equity_df = equity_df.sort_values('timestamp')
        
        # Calculate returns
        equity_df['returns'] = equity_df['total_value'].pct_change()
        
        # Basic metrics
        initial_value = self.initial_capital
        final_value = equity_df['total_value'].iloc[-1]
        total_return = (final_value - initial_value) / initial_value * 100
        
        # Risk metrics
        returns = equity_df['returns'].dropna()
        volatility = returns.std() * np.sqrt(252) * 100  # Annualized
        sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        
        # Drawdown
        running_max = equity_df['total_value'].expanding().max()
        drawdown = (equity_df['total_value'] - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        # Trade metrics
        trades = portfolio["trades"]
        total_trades = len(trades)
        
        # Calculate trade P&L (simplified)
        trade_pnl = []
        for trade in trades:
            if trade["side"] == "BUY":
                # Find corresponding sell trade
                sell_trades = [t for t in trades if t["symbol"] == trade["symbol"] and t["side"] == "SELL" and t["timestamp"] > trade["timestamp"]]
                if sell_trades:
                    sell_trade = sell_trades[0]
                    pnl = (sell_trade["price"] - trade["price"]) * trade["quantity"] - trade.get("commission", 0) - sell_trade.get("commission", 0)
                    trade_pnl.append(pnl)
        
        winning_trades = len([pnl for pnl in trade_pnl if pnl > 0])
        win_rate = (winning_trades / len(trade_pnl) * 100) if trade_pnl else 0
        
        return {
            "total_return": round(total_return, 2),
            "final_value": round(final_value, 2),
            "volatility": round(volatility, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown, 2),
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "avg_trade_return": round(np.mean(trade_pnl), 2) if trade_pnl else 0
        }
