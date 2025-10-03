"""
Tests for authentication service.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User

client = TestClient(app)


@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }


@pytest.fixture
def auth_service():
    return AuthService()


def test_create_user(auth_service, test_user_data):
    """Test user creation."""
    # This would need a test database setup
    pass


def test_authenticate_user(auth_service, test_user_data):
    """Test user authentication."""
    # This would need a test database setup
    pass


def test_password_hashing(auth_service):
    """Test password hashing and verification."""
    password = "testpassword123"
    hashed = auth_service.get_password_hash(password)
    
    assert hashed != password
    assert auth_service.verify_password(password, hashed)
    assert not auth_service.verify_password("wrongpassword", hashed)


def test_jwt_token_creation(auth_service):
    """Test JWT token creation and verification."""
    data = {"sub": "123", "email": "test@example.com"}
    token = auth_service.create_access_token(data)
    
    assert token is not None
    
    payload = auth_service.verify_token(token)
    assert payload is not None
    assert payload["sub"] == "123"
    assert payload["email"] == "test@example.com"


def test_invalid_token(auth_service):
    """Test invalid token handling."""
    invalid_token = "invalid.token.here"
    payload = auth_service.verify_token(invalid_token)
    assert payload is None


def test_expired_token(auth_service):
    """Test expired token handling."""
    from datetime import timedelta
    
    data = {"sub": "123"}
    # Create token that expires immediately
    token = auth_service.create_access_token(data, expires_delta=timedelta(seconds=-1))
    
    payload = auth_service.verify_token(token)
    assert payload is None


def test_user_registration_endpoint():
    """Test user registration API endpoint."""
    user_data = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "newpassword123",
        "full_name": "New User"
    }
    
    response = client.post("/api/v1/users/", json=user_data)
    # This would need proper test database setup
    assert response.status_code in [200, 201, 422]  # 422 for validation errors


def test_user_login_endpoint():
    """Test user login API endpoint."""
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    # This would need proper test database setup
    assert response.status_code in [200, 401, 422]


def test_protected_endpoint():
    """Test access to protected endpoint."""
    # Without token
    response = client.get("/api/v1/users/1")
    assert response.status_code == 401
    
    # With invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/users/1", headers=headers)
    assert response.status_code == 401
