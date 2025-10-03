"""
Asset type enumerations for the Integrated Financial Trading Platform.
Defines all supported asset classes and their types.
"""

from enum import Enum


class AssetType(Enum):
    """Enumeration of supported asset types in the trading platform."""
    
    STOCK = "STOCK"
    BOND = "BOND"
    FOREX = "FOREX"
    INDEX = "INDEX"
    COMMODITY = "COMMODITY"
    CRYPTO = "CRYPTO"
    ETF = "ETF"
    ATF = "ATF"  # Alternative Investment Funds
    REAL_ESTATE = "REAL_ESTATE"


class MLTechnique(Enum):
    """Enumeration of supported ML techniques for algorithmic trading."""
    
    ARIMA = "ARIMA"
    LSTM = "LSTM"
    XGBOOST = "XGBOOST"
    VGG = "VGG"
    TRANSFORMER = "TRANSFORMER"
    RANDOM_FOREST = "RANDOM_FOREST"
    SVM = "SVM"
    CNN = "CNN"
    GRU = "GRU"


class StrategyType(Enum):
    """Enumeration of supported trading strategy types."""
    
    TREND_FOLLOWING = "TREND_FOLLOWING"
    MEAN_REVERSION = "MEAN_REVERSION"
    STATISTICAL_ARBITRAGE = "STATISTICAL_ARBITRAGE"
    MARKET_MAKING = "MARKET_MAKING"
    SENTIMENT_ANALYSIS = "SENTIMENT_ANALYSIS"
    ML_PREDICTIVE = "ML_PREDICTIVE"
    REINFORCEMENT_LEARNING = "REINFORCEMENT_LEARNING"
    HIGH_FREQUENCY_TRADING = "HIGH_FREQUENCY_TRADING"


class OrderType(Enum):
    """Enumeration of supported order types."""
    
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TWAP = "TWAP"  # Time-Weighted Average Price
    VWAP = "VWAP"  # Volume-Weighted Average Price


class OrderSide(Enum):
    """Enumeration of order sides."""
    
    BUY = "BUY"
    SELL = "SELL"
    SHORT = "SHORT"
    COVER = "COVER"


class OrderStatus(Enum):
    """Enumeration of order statuses."""
    
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class RiskLevel(Enum):
    """Enumeration of risk levels for strategies."""
    
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class MarketSession(Enum):
    """Enumeration of market sessions."""
    
    PRE_MARKET = "PRE_MARKET"
    REGULAR = "REGULAR"
    AFTER_HOURS = "AFTER_HOURS"
    CLOSED = "CLOSED"
