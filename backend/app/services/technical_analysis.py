"""
Technical analysis service for calculating trading indicators.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from app.models.market_data import MarketData


class TechnicalAnalysisService:
    """Service for calculating technical analysis indicators."""
    
    def calculate_indicators(self, market_data: List[MarketData]) -> Dict[str, float]:
        """Calculate technical indicators from market data."""
        if len(market_data) < 20:
            return {}
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'timestamp': md.timestamp,
            'open': md.open_price or md.price,
            'high': md.high_price or md.price,
            'low': md.low_price or md.price,
            'close': md.price,
            'volume': md.volume or 0
        } for md in reversed(market_data)])
        
        # Calculate indicators
        indicators = {}
        
        # Moving Averages
        indicators['sma_20'] = df['close'].rolling(window=20).mean().iloc[-1]
        indicators['sma_50'] = df['close'].rolling(window=50).mean().iloc[-1]
        indicators['ema_12'] = df['close'].ewm(span=12).mean().iloc[-1]
        indicators['ema_26'] = df['close'].ewm(span=26).mean().iloc[-1]
        
        # RSI
        indicators['rsi'] = self._calculate_rsi(df['close'])
        
        # MACD
        macd_line, signal_line, histogram = self._calculate_macd(df['close'])
        indicators['macd'] = macd_line
        indicators['macd_signal'] = signal_line
        indicators['macd_histogram'] = histogram
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(df['close'])
        indicators['bollinger_upper'] = bb_upper
        indicators['bollinger_middle'] = bb_middle
        indicators['bollinger_lower'] = bb_lower
        
        # Volume indicators
        indicators['volume_sma'] = df['volume'].rolling(window=20).mean().iloc[-1]
        
        return indicators
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> float:
        """Calculate RSI indicator."""
        if len(prices) < window + 1:
            return 0.0
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 0.0
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """Calculate MACD indicator."""
        if len(prices) < slow + signal:
            return 0.0, 0.0, 0.0
        
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return (
            macd_line.iloc[-1] if not pd.isna(macd_line.iloc[-1]) else 0.0,
            signal_line.iloc[-1] if not pd.isna(signal_line.iloc[-1]) else 0.0,
            histogram.iloc[-1] if not pd.isna(histogram.iloc[-1]) else 0.0
        )
    
    def _calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, std_dev: int = 2) -> tuple:
        """Calculate Bollinger Bands."""
        if len(prices) < window:
            return 0.0, 0.0, 0.0
        
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return (
            upper_band.iloc[-1] if not pd.isna(upper_band.iloc[-1]) else 0.0,
            sma.iloc[-1] if not pd.isna(sma.iloc[-1]) else 0.0,
            lower_band.iloc[-1] if not pd.isna(lower_band.iloc[-1]) else 0.0
        )
    
    def detect_patterns(self, market_data: List[MarketData]) -> Dict[str, Any]:
        """Detect candlestick patterns."""
        if len(market_data) < 5:
            return {}
        
        df = pd.DataFrame([{
            'open': md.open_price or md.price,
            'high': md.high_price or md.price,
            'low': md.low_price or md.price,
            'close': md.price
        } for md in reversed(market_data[-5:])])  # Last 5 candles
        
        patterns = {}
        
        # Doji pattern
        patterns['doji'] = self._detect_doji(df.iloc[-1])
        
        # Hammer pattern
        patterns['hammer'] = self._detect_hammer(df.iloc[-1])
        
        # Engulfing pattern
        if len(df) >= 2:
            patterns['bullish_engulfing'] = self._detect_bullish_engulfing(df.iloc[-2:])
            patterns['bearish_engulfing'] = self._detect_bearish_engulfing(df.iloc[-2:])
        
        return patterns
    
    def _detect_doji(self, candle: pd.Series) -> bool:
        """Detect doji candlestick pattern."""
        body_size = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        
        return body_size <= (total_range * 0.1) and total_range > 0
    
    def _detect_hammer(self, candle: pd.Series) -> bool:
        """Detect hammer candlestick pattern."""
        body_size = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        total_range = candle['high'] - candle['low']
        
        return (lower_shadow >= 2 * body_size and 
                upper_shadow <= body_size and 
                total_range > 0)
    
    def _detect_bullish_engulfing(self, candles: pd.DataFrame) -> bool:
        """Detect bullish engulfing pattern."""
        if len(candles) < 2:
            return False
        
        prev_candle = candles.iloc[0]
        curr_candle = candles.iloc[1]
        
        # Previous candle should be bearish
        prev_bearish = prev_candle['close'] < prev_candle['open']
        
        # Current candle should be bullish and engulf the previous
        curr_bullish = curr_candle['close'] > curr_candle['open']
        engulfs = (curr_candle['open'] < prev_candle['close'] and 
                  curr_candle['close'] > prev_candle['open'])
        
        return prev_bearish and curr_bullish and engulfs
    
    def _detect_bearish_engulfing(self, candles: pd.DataFrame) -> bool:
        """Detect bearish engulfing pattern."""
        if len(candles) < 2:
            return False
        
        prev_candle = candles.iloc[0]
        curr_candle = candles.iloc[1]
        
        # Previous candle should be bullish
        prev_bullish = prev_candle['close'] > prev_candle['open']
        
        # Current candle should be bearish and engulf the previous
        curr_bearish = curr_candle['close'] < curr_candle['open']
        engulfs = (curr_candle['open'] > prev_candle['close'] and 
                  curr_candle['close'] < prev_candle['open'])
        
        return prev_bullish and curr_bearish and engulfs
