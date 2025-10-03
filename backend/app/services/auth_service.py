"""
Authentication and authorization service.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for handling authentication and authorization."""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def get_current_user(self, db: Session, token: str) -> Optional[User]:
        """Get current user from JWT token."""
        payload = self.verify_token(token)
        if payload is None:
            return None
        
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
    
    def create_user(self, db: Session, email: str, username: str, password: str, full_name: str = None) -> User:
        """Create a new user."""
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )
        
        # Create new user
        hashed_password = self.get_password_hash(password)
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    def update_user_password(self, db: Session, user_id: int, old_password: str, new_password: str) -> bool:
        """Update user password."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        if not self.verify_password(old_password, user.hashed_password):
            return False
        
        user.hashed_password = self.get_password_hash(new_password)
        db.commit()
        return True
    
    def reset_password_request(self, db: Session, email: str) -> bool:
        """Initiate password reset process."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False
        
        # Generate reset token
        reset_data = {
            "sub": str(user.id),
            "type": "password_reset",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        reset_token = jwt.encode(reset_data, self.secret_key, algorithm=self.algorithm)
        
        # In a real implementation, send email with reset token
        # For now, just return True
        return True
    
    def reset_password(self, db: Session, reset_token: str, new_password: str) -> bool:
        """Reset password using reset token."""
        payload = self.verify_token(reset_token)
        if payload is None or payload.get("type") != "password_reset":
            return False
        
        user_id = payload.get("sub")
        if user_id is None:
            return False
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            return False
        
        user.hashed_password = self.get_password_hash(new_password)
        db.commit()
        return True
