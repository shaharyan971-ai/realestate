"""Integration tests for authentication endpoints."""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    async def test_register_success(self):
        """Test successful user registration."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "TestPassword123",
                    "full_name": "Test User",
                    "phone": "+1234567890"
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
    
    async def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First registration
            await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "duplicate@example.com",
                    "password": "TestPassword123",
                    "full_name": "Test User",
                    "phone": "+1234567890"
                }
            )
            
            # Second registration with same email
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "duplicate@example.com",
                    "password": "TestPassword123",
                    "full_name": "Test User 2",
                    "phone": "+0987654321"
                }
            )
            
            assert response.status_code == 400
            assert "already registered" in response.json()["detail"].lower()
    
    async def test_login_success(self):
        """Test successful login."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register user first
            await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "logintest@example.com",
                    "password": "TestPassword123",
                    "full_name": "Login Test",
                    "phone": "+1234567890"
                }
            )
            
            # Login
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "logintest@example.com",
                    "password": "TestPassword123"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
    
    async def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "nonexistent@example.com",
                    "password": "WrongPassword123"
                }
            )
            
            assert response.status_code == 401
    
    async def test_get_current_user(self):
        """Test getting current user info."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register and get token
            register_response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "currentuser@example.com",
                    "password": "TestPassword123",
                    "full_name": "Current User",
                    "phone": "+1234567890"
                }
            )
            
            token = register_response.json()["access_token"]
            
            # Get current user
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "currentuser@example.com"
            assert data["full_name"] == "Current User"
