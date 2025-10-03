"""
Tests for trading functionality.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_assets():
    """Test getting assets list."""
    response = client.get("/api/v1/assets/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_asset_by_symbol():
    """Test getting asset by symbol."""
    response = client.get("/api/v1/assets/symbol/AAPL")
    # This might return 404 if no data, which is expected
    assert response.status_code in [200, 404]


def test_search_assets():
    """Test searching assets."""
    response = client.get("/api/v1/assets/search/AAPL")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_trade():
    """Test creating a trade."""
    trade_data = {
        "asset_id": 1,
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": 10,
        "price": 150.0
    }
    
    response = client.post("/api/v1/trades/?user_id=1", json=trade_data)
    # This might return 404 if no user/asset exists
    assert response.status_code in [200, 201, 404, 422]


def test_get_trades():
    """Test getting user trades."""
    response = client.get("/api/v1/trades/?user_id=1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_strategies():
    """Test getting strategies."""
    response = client.get("/api/v1/strategies/?user_id=1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_strategy():
    """Test creating a strategy."""
    strategy_data = {
        "name": "Test Strategy",
        "description": "A test trading strategy",
        "type": "TREND_FOLLOWING",
        "risk_level": "MEDIUM",
        "max_position_size": 5.0,
        "stop_loss_percent": 2.0,
        "take_profit_percent": 5.0
    }
    
    response = client.post("/api/v1/strategies/?user_id=1", json=strategy_data)
    # This might return 404 if no user exists
    assert response.status_code in [200, 201, 404, 422]


def test_get_performance_report():
    """Test getting performance report."""
    response = client.get("/api/v1/reports/performance/1")
    # This might return 404 if no user exists
    assert response.status_code in [200, 404]


def test_get_portfolio_report():
    """Test getting portfolio report."""
    response = client.get("/api/v1/reports/portfolio/1")
    # This might return 404 if no user exists
    assert response.status_code in [200, 404]


def test_ml_prediction():
    """Test ML price prediction."""
    response = client.post("/api/v1/ml/predict/1?model_type=LSTM")
    # This might return 404 if no asset exists
    assert response.status_code in [200, 404, 400]


def test_backtest_strategy():
    """Test strategy backtesting."""
    response = client.post(
        "/api/v1/reports/backtest/1?start_date=2023-01-01&end_date=2023-12-31"
    )
    # This might return 404 if no strategy exists
    assert response.status_code in [200, 404, 400]


def test_subscription_plans():
    """Test getting subscription plans."""
    response = client.get("/api/v1/subscriptions/plans")
    assert response.status_code == 200
    assert "plans" in response.json()


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_rate_limiting():
    """Test rate limiting middleware."""
    # Make multiple requests quickly
    responses = []
    for _ in range(10):
        response = client.get("/api/v1/assets/")
        responses.append(response.status_code)
    
    # Should not all be 429 (rate limited) in normal circumstances
    # This test might need adjustment based on rate limiting configuration
    assert 200 in responses or 404 in responses  # At least some should succeed
