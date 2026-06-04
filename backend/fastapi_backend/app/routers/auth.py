"""Authentication router for user registration and login."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId

from app.core.database import get_db
from app.core.security import (
    hash_password, 
    verify_password, 
    create_token_pair,
    verify_token
)
from app.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse
)
from app.models import UserModel, UserRole
from app.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegisterRequest, db=Depends(get_db)):
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        
    Returns:
        JWT tokens
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = UserModel(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=UserRole.USER,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Insert into database
    result = await db.users.insert_one(user.model_dump(by_alias=True, exclude={"_id"}))
    user_id = str(result.inserted_id)
    
    # Create tokens
    tokens = create_token_pair(
        user_id=user_id,
        email=user.email,
        role=user.role.value
    )
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=settings.JWT_EXPIRATION_HOURS * 3600
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLoginRequest, db=Depends(get_db)):
    """
    Login user and return JWT tokens.
    
    Args:
        credentials: Email and password
        
    Returns:
        JWT tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Update last login
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create tokens
    tokens = create_token_pair(
        user_id=str(user["_id"]),
        email=user["email"],
        role=user["role"]
    )
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=settings.JWT_EXPIRATION_HOURS * 3600
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security), db=Depends(get_db)):
    """
    Refresh access token using refresh token.
    
    Args:
        credentials: Bearer token (refresh token)
        
    Returns:
        New JWT tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    token = credentials.credentials
    
    # Verify refresh token
    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Verify user still exists and is active
    user = await db.users.find_one({"_id": ObjectId(token_data.user_id)})
    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    tokens = create_token_pair(
        user_id=str(user["_id"]),
        email=user["email"],
        role=user["role"]
    )
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=settings.JWT_EXPIRATION_HOURS * 3600
    )


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout user (client-side token deletion).
    
    Note: Since we're using stateless JWT, actual logout happens on client side.
    This endpoint is provided for consistency and can be extended with token blacklisting.
    
    Args:
        credentials: Bearer token
        
    Returns:
        Success message
    """
    # Verify token is valid
    token_data = verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # TODO: Add token to blacklist (Redis) for enhanced security
    
    return {
        "message": "Successfully logged out",
        "detail": "Please delete the token from client storage"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
):
    """
    Get current authenticated user information.
    
    Args:
        credentials: Bearer token
        
    Returns:
        User information
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token_data = verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Get user from database
    user = await db.users.find_one({"_id": ObjectId(token_data.user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        _id=str(user["_id"]),
        email=user["email"],
        full_name=user["full_name"],
        phone=user["phone"],
        role=user["role"],
        is_verified=user.get("is_verified", False),
        profile_image=user.get("profile_image")
    )
