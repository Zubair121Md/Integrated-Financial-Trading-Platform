"""
Pytest configuration and fixtures.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.config import settings

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create test database session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }


@pytest.fixture
def test_asset_data():
    """Test asset data."""
    return {
        "symbol": "TEST",
        "name": "Test Asset",
        "type": "STOCK",
        "current_price": 100.0,
        "currency": "USD"
    }


@pytest.fixture
def test_trade_data():
    """Test trade data."""
    return {
        "asset_id": 1,
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": 10,
        "price": 100.0,
        "total_value": 1000.0
    }


@pytest.fixture
def test_strategy_data():
    """Test strategy data."""
    return {
        "name": "Test Strategy",
        "description": "A test trading strategy",
        "type": "TREND_FOLLOWING",
        "risk_level": "MEDIUM",
        "max_position_size": 5.0,
        "stop_loss_percent": 2.0,
        "take_profit_percent": 5.0
    }
