"""User management router."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId

from app.core.database import get_db
from app.core.security import hash_password, verify_password, verify_token
from app.schemas import UserResponse
from app.models import UserRole
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/v1/users", tags=["Users"])
security = HTTPBearer()


# Request schemas
class UserUpdateRequest(BaseModel):
    """User profile update request."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str


class UpdateEmailRequest(BaseModel):
    """Update email request."""
    new_email: EmailStr
    password: str


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
):
    """Get current authenticated user."""
    token_data = verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user = await db.users.find_one({"_id": ObjectId(token_data.user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user profile.
    
    Returns:
        User profile information
    """
    return UserResponse(
        _id=str(current_user["_id"]),
        email=current_user["email"],
        full_name=current_user["full_name"],
        phone=current_user["phone"],
        role=current_user["role"],
        is_verified=current_user.get("is_verified", False),
        profile_image=current_user.get("profile_image")
    )


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    update_data: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Update current user profile.
    
    Args:
        update_data: Fields to update
        
    Returns:
        Updated user profile
    """
    # Build update dict (only non-None values)
    update_dict = {
        k: v for k, v in update_data.model_dump().items() 
        if v is not None
    }
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Add updated_at timestamp
    update_dict["updated_at"] = datetime.utcnow()
    
    # Update user
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": update_dict}
    )
    
    # Get updated user
    updated_user = await db.users.find_one({"_id": current_user["_id"]})
    
    return UserResponse(
        _id=str(updated_user["_id"]),
        email=updated_user["email"],
        full_name=updated_user["full_name"],
        phone=updated_user["phone"],
        role=updated_user["role"],
        is_verified=updated_user.get("is_verified", False),
        profile_image=updated_user.get("profile_image")
    )


@router.post("/me/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Change user password.
    
    Args:
        password_data: Current and new password
        
    Returns:
        Success message
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters"
        )
    
    # Hash new password
    new_password_hash = hash_password(password_data.new_password)
    
    # Update password
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {
            "$set": {
                "password_hash": new_password_hash,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {
        "message": "Password changed successfully",
        "detail": "Please login again with your new password"
    }


@router.put("/me/email")
async def update_email(
    email_data: UpdateEmailRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Update user email address.
    
    Args:
        email_data: New email and password confirmation
        
    Returns:
        Success message
    """
    # Verify password
    if not verify_password(email_data.password, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )
    
    # Check if new email already exists
    existing_user = await db.users.find_one({"email": email_data.new_email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already in use"
        )
    
    # Update email
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {
            "$set": {
                "email": email_data.new_email,
                "is_verified": False,  # Require re-verification
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {
        "message": "Email updated successfully",
        "detail": "Please verify your new email address"
    }


@router.delete("/me")
async def delete_my_account(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Delete current user account (soft delete).
    
    Returns:
        Success message
    """
    # Soft delete by marking as inactive
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {
        "message": "Account deleted successfully",
        "detail": "Your account has been deactivated"
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get user by ID (admin or self only).
    
    Args:
        user_id: User ID to retrieve
        
    Returns:
        User profile
        
    Raises:
        HTTPException: If user not found or unauthorized
    """
    # Check if user is admin or requesting their own profile
    if current_user["role"] != UserRole.ADMIN.value and str(current_user["_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this profile"
        )
    
    # Get user
    user = await db.users.find_one({"_id": ObjectId(user_id)})
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
