"""
Advanced algorithmic trading engine with full-spectrum capabilities.
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from dataclasses import dataclass
from enum import Enum
import json

from app.models.trade import Trade, OrderSide, OrderType, OrderStatus
from app.models.strategy import Strategy, AlgoStrategy
from app.models.asset import Asset
from app.models.market_data import MarketData
from app.services.ml_models import MLModelService
from app.services.advanced_ml_models import AdvancedMLService
from app.services.technical_analysis import TechnicalAnalysisService
from app.services.risk_management import RiskManagementService


class StrategyType(Enum):
    TREND_FOLLOWING = "TREND_FOLLOWING"
    MEAN_REVERSION = "MEAN_REVERSION"
    MOMENTUM = "MOMENTUM"
    ARBITRAGE = "ARBITRAGE"
    MARKET_MAKING = "MARKET_MAKING"
    PAIRS_TRADING = "PAIRS_TRADING"
    ML_PREDICTIVE = "ML_PREDICTIVE"
    QUANTITATIVE = "QUANTITATIVE"


@dataclass
class TradingSignal:
    asset_id: int
    symbol: str
    side: OrderSide
    confidence: float
    price: float
    quantity: float
    strategy_id: int
    signal_strength: float
    risk_score: float
    metadata: Dict[str, Any]


@dataclass
class PortfolioState:
    total_value: float
    cash_balance: float
    positions: Dict[int, float]  # asset_id -> quantity
    unrealized_pnl: float
    realized_pnl: float
    risk_metrics: Dict[str, float]


class AdvancedTradingEngine:
    """Advanced algorithmic trading engine with full-spectrum capabilities."""
    
    def __init__(self):
        self.ml_service = MLModelService()
        self.advanced_ml_service = AdvancedMLService()
        self.ta_service = TechnicalAnalysisService()
        self.risk_service = RiskManagementService()
        self.active_strategies = {}
        self.portfolio_state = PortfolioState(0, 0, {}, 0, 0, {})
        self.signal_queue = asyncio.Queue()
        self.is_running = False
    
    async def start_engine(self, db: Session):
        """Start the advanced trading engine."""
        self.is_running = True
        
        # Load active strategies
        await self._load_active_strategies(db)
        
        # Start background tasks
        asyncio.create_task(self._signal_processor())
        asyncio.create_task(self._market_data_processor(db))
        asyncio.create_task(self._portfolio_monitor(db))
        asyncio.create_task(self._risk_monitor(db))
        
        print("Advanced Trading Engine started successfully")
    
    async def stop_engine(self):
        """Stop the trading engine."""
        self.is_running = False
        print("Advanced Trading Engine stopped")
    
    async def _load_active_strategies(self, db: Session):
        """Load all active strategies."""
        strategies = db.query(Strategy).filter(Strategy.is_active == True).all()
        
        for strategy in strategies:
            self.active_strategies[strategy.id] = {
                'strategy': strategy,
                'last_execution': None,
                'performance_metrics': {},
                'risk_limits': self._calculate_risk_limits(strategy)
            }
        
        print(f"Loaded {len(self.active_strategies)} active strategies")
    
    async def _signal_processor(self):
        """Process trading signals from the queue."""
        while self.is_running:
            try:
                signal = await asyncio.wait_for(self.signal_queue.get(), timeout=1.0)
                await self._process_signal(signal)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing signal: {e}")
    
    async def _market_data_processor(self, db: Session):
        """Process market data and generate signals."""
        while self.is_running:
            try:
                # Get latest market data
                latest_data = db.query(MarketData).filter(
                    MarketData.timestamp >= datetime.now() - timedelta(minutes=5)
                ).all()
                
                if latest_data:
                    await self._analyze_market_data(latest_data, db)
                
                await asyncio.sleep(30)  # Process every 30 seconds
            except Exception as e:
                print(f"Error processing market data: {e}")
                await asyncio.sleep(60)
    
    async def _portfolio_monitor(self, db: Session):
        """Monitor portfolio state and rebalance if needed."""
        while self.is_running:
            try:
                await self._update_portfolio_state(db)
                await self._check_rebalancing_opportunities(db)
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"Error monitoring portfolio: {e}")
                await asyncio.sleep(300)
    
    async def _risk_monitor(self, db: Session):
        """Monitor risk metrics and apply risk controls."""
        while self.is_running:
            try:
                await self._update_risk_metrics(db)
                await self._apply_risk_controls(db)
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Error monitoring risk: {e}")
                await asyncio.sleep(60)
    
    async def _analyze_market_data(self, market_data: List[MarketData], db: Session):
        """Analyze market data and generate trading signals."""
        
        # Group data by asset
        asset_data = {}
        for data in market_data:
            if data.asset_id not in asset_data:
                asset_data[data.asset_id] = []
            asset_data[data.asset_id].append(data)
        
        # Analyze each asset
        for asset_id, data_list in asset_data.items():
            try:
                signals = await self._generate_signals_for_asset(asset_id, data_list, db)
                for signal in signals:
                    await self.signal_queue.put(signal)
            except Exception as e:
                print(f"Error analyzing asset {asset_id}: {e}")
    
    async def _generate_signals_for_asset(
        self, 
        asset_id: int, 
        market_data: List[MarketData], 
        db: Session
    ) -> List[TradingSignal]:
        """Generate trading signals for a specific asset."""
        
        signals = []
        
        # Get asset info
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return signals
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'timestamp': md.timestamp,
            'price': md.price,
            'open': md.open_price or md.price,
            'high': md.high_price or md.price,
            'low': md.low_price or md.price,
            'volume': md.volume or 0,
            'rsi': md.rsi or 0,
            'macd': md.macd or 0,
            'sma_20': md.sma_20 or 0,
            'sma_50': md.sma_50 or 0
        } for md in market_data])
        
        if len(df) < 20:
            return signals
        
        # Generate signals from each active strategy
        for strategy_id, strategy_info in self.active_strategies.items():
            strategy = strategy_info['strategy']
            
            try:
                strategy_signals = await self._execute_strategy(
                    strategy, asset, df, db
                )
                signals.extend(strategy_signals)
            except Exception as e:
                print(f"Error executing strategy {strategy_id}: {e}")
        
        return signals
    
    async def _execute_strategy(
        self, 
        strategy: Strategy, 
        asset: Asset, 
        data: pd.DataFrame, 
        db: Session
    ) -> List[TradingSignal]:
        """Execute a specific trading strategy."""
        
        signals = []
        
        if strategy.type == StrategyType.TREND_FOLLOWING:
            signals = await self._trend_following_strategy(strategy, asset, data)
        elif strategy.type == StrategyType.MEAN_REVERSION:
            signals = await self._mean_reversion_strategy(strategy, asset, data)
        elif strategy.type == StrategyType.MOMENTUM:
            signals = await self._momentum_strategy(strategy, asset, data)
        elif strategy.type == StrategyType.ARBITRAGE:
            signals = await self._arbitrage_strategy(strategy, asset, data, db)
        elif strategy.type == StrategyType.MARKET_MAKING:
            signals = await self._market_making_strategy(strategy, asset, data)
        elif strategy.type == StrategyType.PAIRS_TRADING:
            signals = await self._pairs_trading_strategy(strategy, asset, data, db)
        elif strategy.type == StrategyType.ML_PREDICTIVE:
            signals = await self._ml_predictive_strategy(strategy, asset, data, db)
        elif strategy.type == StrategyType.QUANTITATIVE:
            signals = await self._quantitative_strategy(strategy, asset, data)
        
        return signals
    
    async def _trend_following_strategy(
        self, 
        strategy: Strategy, 
        asset: Asset, 
        data: pd.DataFrame
    ) -> List[TradingSignal]:
        """Execute trend following strategy."""
        
        signals = []
        params = strategy.parameters or {}
        
        # Calculate indicators
        data['sma_short'] = data['price'].rolling(window=params.get('short_window', 20)).mean()
        data['sma_long'] = data['price'].rolling(window=params.get('long_window', 50)).mean()
        data['rsi'] = self.ta_service._calculate_rsi(data['price'])
        
        if len(data) < 2:
            return signals
        
        current = data.iloc[-1]
        previous = data.iloc[-2]
        
        # Buy signal: short MA crosses above long MA
        if (current['sma_short'] > current['sma_long'] and 
            previous['sma_short'] <= previous['sma_long'] and
            current['rsi'] < params.get('rsi_threshold', 70)):
            
            signal = TradingSignal(
                asset_id=asset.id,
                symbol=asset.symbol,
                side=OrderSide.BUY,
                confidence=0.8,
                price=current['price'],
                quantity=self._calculate_position_size(strategy, current['price']),
                strategy_id=strategy.id,
                signal_strength=0.8,
                risk_score=0.3,
                metadata={'strategy_type': 'trend_following'}
            )
            signals.append(signal)
        
        # Sell signal: short MA crosses below long MA
        elif (current['sma_short'] < current['sma_long'] and 
              previous['sma_short'] >= previous['sma_long'] and
              current['rsi'] > (100 - params.get('rsi_threshold', 70))):
            
            signal = TradingSignal(
                asset_id=asset.id,
                symbol=asset.symbol,
                side=OrderSide.SELL,
                confidence=0.8,
                price=current['price'],
                quantity=self._calculate_position_size(strategy, current['price']),
                strategy_id=strategy.id,
                signal_strength=0.8,
                risk_score=0.3,
                metadata={'strategy_type': 'trend_following'}
            )
            signals.append(signal)
        
        return signals
    
    async def _ml_predictive_strategy(
        self, 
        strategy: Strategy, 
        asset: Asset, 
        data: pd.DataFrame, 
        db: Session
    ) -> List[TradingSignal]:
        """Execute ML predictive strategy."""
        
        signals = []
        
        # Get the associated algo strategy
        algo_strategy = db.query(AlgoStrategy).filter(
            AlgoStrategy.strategy_id == strategy.id
        ).first()
        
        if not algo_strategy or not algo_strategy.is_trained:
            return signals
        
        try:
            # Make prediction
            prediction_result = await self.ml_service.predict_price(
                f"models/{algo_strategy.ml_technique.lower()}_asset_{asset.id}_latest.joblib",
                algo_strategy.ml_technique.value,
                data,
                lookback_days=30
            )
            
            if prediction_result["status"] == "success":
                current_price = data['price'].iloc[-1]
                predicted_price = prediction_result["prediction"]
                confidence = prediction_result["confidence"]
                
                # Generate signal based on prediction
                price_change = (predicted_price - current_price) / current_price
                threshold = 0.02  # 2% threshold
                
                if price_change > threshold and confidence > 0.7:
                    signal = TradingSignal(
                        asset_id=asset.id,
                        symbol=asset.symbol,
                        side=OrderSide.BUY,
                        confidence=confidence,
                        price=current_price,
                        quantity=self._calculate_position_size(strategy, current_price),
                        strategy_id=strategy.id,
                        signal_strength=abs(price_change),
                        risk_score=1.0 - confidence,
                        metadata={'strategy_type': 'ml_predictive', 'predicted_price': predicted_price}
                    )
                    signals.append(signal)
                
                elif price_change < -threshold and confidence > 0.7:
                    signal = TradingSignal(
                        asset_id=asset.id,
                        symbol=asset.symbol,
                        side=OrderSide.SELL,
                        confidence=confidence,
                        price=current_price,
                        quantity=self._calculate_position_size(strategy, current_price),
                        strategy_id=strategy.id,
                        signal_strength=abs(price_change),
                        risk_score=1.0 - confidence,
                        metadata={'strategy_type': 'ml_predictive', 'predicted_price': predicted_price}
                    )
                    signals.append(signal)
        
        except Exception as e:
            print(f"Error in ML predictive strategy: {e}")
        
        return signals
    
    def _calculate_position_size(self, strategy: Strategy, price: float) -> float:
        """Calculate position size based on strategy parameters."""
        max_position_size = strategy.max_position_size or 1000.0
        return max_position_size / price
    
    def _calculate_risk_limits(self, strategy: Strategy) -> Dict[str, float]:
        """Calculate risk limits for a strategy."""
        return {
            'max_drawdown': strategy.stop_loss_percent or 5.0,
            'max_position_size': strategy.max_position_size or 1000.0,
            'max_daily_loss': strategy.max_position_size or 1000.0 * 0.1,
            'max_correlation': 0.7
        }
    
    async def _process_signal(self, signal: TradingSignal):
        """Process a trading signal."""
        try:
            # Apply risk controls
            if not await self._check_risk_controls(signal):
                print(f"Signal rejected due to risk controls: {signal.symbol}")
                return
            
            # Execute trade
            await self._execute_trade(signal)
            
        except Exception as e:
            print(f"Error processing signal: {e}")
    
    async def _check_risk_controls(self, signal: TradingSignal) -> bool:
        """Check if signal passes risk controls."""
        # Implement risk control logic
        return True  # Simplified for now
    
    async def _execute_trade(self, signal: TradingSignal):
        """Execute a trade based on signal."""
        # Implement trade execution logic
        print(f"Executing trade: {signal.side.value} {signal.quantity} {signal.symbol} at {signal.price}")
    
    async def _update_portfolio_state(self, db: Session):
        """Update portfolio state."""
        # Implement portfolio state update logic
        pass
    
    async def _check_rebalancing_opportunities(self, db: Session):
        """Check for portfolio rebalancing opportunities."""
        # Implement rebalancing logic
        pass
    
    async def _update_risk_metrics(self, db: Session):
        """Update risk metrics."""
        # Implement risk metrics update logic
        pass
    
    async def _apply_risk_controls(self, db: Session):
        """Apply risk controls."""
        # Implement risk control application logic
        pass
    
    # Placeholder methods for other strategy types
    async def _mean_reversion_strategy(self, strategy, asset, data):
        return []
    
    async def _momentum_strategy(self, strategy, asset, data):
        return []
    
    async def _arbitrage_strategy(self, strategy, asset, data, db):
        return []
    
    async def _market_making_strategy(self, strategy, asset, data):
        return []
    
    async def _pairs_trading_strategy(self, strategy, asset, data, db):
        return []
    
    async def _quantitative_strategy(self, strategy, asset, data):
        return []
