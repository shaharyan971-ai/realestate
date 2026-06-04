"""Unit tests for security module."""
import pytest
from datetime import datetime, timedelta
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    create_token_pair,
    require_role
)
from fastapi import HTTPException


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False


class TestJWTTokens:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {
            "sub": "user123",
            "email": "test@example.com",
            "role": "user"
        }
        
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {
            "sub": "user123",
            "email": "test@example.com",
            "role": "user"
        }
        
        token = create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self):
        """Test token verification with valid token."""
        data = {
            "sub": "user123",
            "email": "test@example.com",
            "role": "user"
        }
        
        token = create_access_token(data)
        token_data = verify_token(token)
        
        assert token_data is not None
        assert token_data.user_id == "user123"
        assert token_data.email == "test@example.com"
        assert token_data.role == "user"
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        invalid_token = "invalid.token.here"
        token_data = verify_token(invalid_token)
        
        assert token_data is None
    
    def test_create_token_pair(self):
        """Test token pair creation."""
        tokens = create_token_pair(
            user_id="user123",
            email="test@example.com",
            role="user"
        )
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "bearer"


class TestRoleBasedAccess:
    """Test role-based access control."""
    
    def test_require_role_authorized(self):
        """Test require_role with authorized user."""
        user = {"role": "admin"}
        allowed_roles = ["admin", "agent"]
        
        # Should not raise exception
        require_role(user, allowed_roles)
    
    def test_require_role_unauthorized(self):
        """Test require_role with unauthorized user."""
        user = {"role": "user"}
        allowed_roles = ["admin", "agent"]
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            require_role(user, allowed_roles)
        
        assert exc_info.value.status_code == 403
