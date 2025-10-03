"""
Configuration settings for the trading platform backend.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = "postgresql://postgres:postgres@localhost:5432/trading_platform"
    redis_url: str = "redis://localhost:6379/0"
    
    # API Keys
    alpha_vantage_key: Optional[str] = None
    coingecko_api_key: Optional[str] = None
    quandl_api_key: Optional[str] = None
    eurekahedge_api_key: Optional[str] = None
    binance_api_key: Optional[str] = None
    binance_secret_key: Optional[str] = None
    alpaca_api_key: Optional[str] = None
    alpaca_secret_key: Optional[str] = None
    
    # Payment Processing
    stripe_publishable_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket_name: Optional[str] = None
    
    # JWT Configuration
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # Application Configuration
    debug: bool = True
    environment: str = "development"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:4000"]
    
    # ML Model Configuration
    ml_model_bucket: Optional[str] = None
    model_retrain_interval_hours: int = 24
    
    # Risk Management
    max_position_size_percent: float = 5.0
    max_daily_drawdown_percent: float = 2.0
    kill_switch_enabled: bool = True
    
    # External Data Sources
    news_api_key: Optional[str] = None
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    
    @validator("cors_origins", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
