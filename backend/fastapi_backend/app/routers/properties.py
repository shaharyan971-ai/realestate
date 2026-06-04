"""Property management router with async database operations."""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId

from app.core.database import get_db
from app.core.security import verify_token, require_role
from app.schemas import PropertyCreateRequest, PropertyUpdateRequest, PropertyResponse
from app.models import PropertyModel, PropertyStatus, PropertyType, UserRole

router = APIRouter(prefix="/api/v1/properties", tags=["Properties"])
security = HTTPBearer()


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
):
    """Get current authenticated user from token."""
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
    
    return user


# Utility: Convert MongoDB document to dict with string ID
def fix_id(doc: dict) -> dict:
    """Convert MongoDB _id to string id."""
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_property(
    property_data: PropertyCreateRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Create a new property listing (Agent or Admin only).
    
    Args:
        property_data: Property creation data
        
    Returns:
        Created property
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    # Check role
    require_role(current_user, [UserRole.AGENT.value, UserRole.ADMIN.value])
    
    # Create property model
    property_dict = property_data.model_dump()
    property_dict["owner_id"] = current_user["_id"]
    property_dict["agent_id"] = current_user["_id"] if current_user["role"] == UserRole.AGENT.value else None
    property_dict["status"] = PropertyStatus.ACTIVE.value
    property_dict["created_at"] = datetime.utcnow()
    property_dict["updated_at"] = datetime.utcnow()
    property_dict["views"] = 0
    property_dict["favorites_count"] = 0
    property_dict["booking_count"] = 0
    
    # Insert into database
    result = await db.properties.insert_one(property_dict)
    
    # Get created property
    created_property = await db.properties.find_one({"_id": result.inserted_id})
    
    return fix_id(created_property)


@router.get("/")
async def list_properties(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    city: Optional[str] = None,
    property_type: Optional[PropertyType] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    db=Depends(get_db)
):
    """
    List all active properties with optional filters.
    
    Args:
        skip: Number of properties to skip (pagination)
        limit: Maximum number of properties to return
        city: Filter by city
        property_type: Filter by property type
        min_price: Minimum price filter
        max_price: Maximum price filter
        bedrooms: Filter by number of bedrooms
        
    Returns:
        List of properties
    """
    # Build query
    query = {"status": PropertyStatus.ACTIVE.value}
    
    if city:
        query["city"] = {"$regex": city, "$options": "i"}  # Case-insensitive search
    
    if property_type:
        query["property_type"] = property_type.value
    
    if min_price is not None or max_price is not None:
        query["price"] = {}
        if min_price is not None:
            query["price"]["$gte"] = min_price
        if max_price is not None:
            query["price"]["$lte"] = max_price
    
    if bedrooms is not None:
        query["bedrooms"] = bedrooms
    
    # Get total count
    total = await db.properties.count_documents(query)
    
    # Get properties
    cursor = db.properties.find(query).sort("created_at", -1).skip(skip).limit(limit)
    properties = await cursor.to_list(length=limit)
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "properties": [fix_id(prop) for prop in properties]
    }


@router.get("/{property_id}")
async def get_property(property_id: str, db=Depends(get_db)):
    """
    Get property by ID and increment view count.
    
    Args:
        property_id: Property ID
        
    Returns:
        Property details
        
    Raises:
        HTTPException: If property not found
    """
    # Validate ObjectId
    if not ObjectId.is_valid(property_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid property ID"
        )
    
    # Increment view count
    await db.properties.update_one(
        {"_id": ObjectId(property_id)},
        {"$inc": {"views": 1}}
    )
    
    # Get property
    property_doc = await db.properties.find_one({"_id": ObjectId(property_id)})
    
    if not property_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    return fix_id(property_doc)


@router.put("/{property_id}")
async def update_property(
    property_id: str,
    property_data: PropertyUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Update property (Owner, Agent, or Admin only).
    
    Args:
        property_id: Property ID
        property_data: Fields to update
        
    Returns:
        Updated property
        
    Raises:
        HTTPException: If property not found or user doesn't have permission
    """
    # Validate ObjectId
    if not ObjectId.is_valid(property_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid property ID"
        )
    
    # Get property
    property_doc = await db.properties.find_one({"_id": ObjectId(property_id)})
    
    if not property_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Check permissions (owner, agent, or admin)
    user_id = current_user["_id"]
    user_role = current_user["role"]
    
    is_owner = property_doc.get("owner_id") == user_id
    is_agent = property_doc.get("agent_id") == user_id
    is_admin = user_role == UserRole.ADMIN.value
    
    if not (is_owner or is_agent or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this property"
        )
    
    # Build update dict
    update_dict = {
        k: v for k, v in property_data.model_dump().items() 
        if v is not None
    }
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    update_dict["updated_at"] = datetime.utcnow()
    
    # Update property
    await db.properties.update_one(
        {"_id": ObjectId(property_id)},
        {"$set": update_dict}
    )
    
    # Get updated property
    updated_property = await db.properties.find_one({"_id": ObjectId(property_id)})
    
    return fix_id(updated_property)


@router.delete("/{property_id}")
async def delete_property(
    property_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Delete property (Owner, Agent, or Admin only).
    
    Args:
        property_id: Property ID
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If property not found or user doesn't have permission
    """
    # Validate ObjectId
    if not ObjectId.is_valid(property_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid property ID"
        )
    
    # Get property
    property_doc = await db.properties.find_one({"_id": ObjectId(property_id)})
    
    if not property_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Check permissions
    user_id = current_user["_id"]
    user_role = current_user["role"]
    
    is_owner = property_doc.get("owner_id") == user_id
    is_agent = property_doc.get("agent_id") == user_id
    is_admin = user_role == UserRole.ADMIN.value
    
    if not (is_owner or is_agent or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this property"
        )
    
    # Soft delete by setting status to inactive
    await db.properties.update_one(
        {"_id": ObjectId(property_id)},
        {
            "$set": {
                "status": PropertyStatus.INACTIVE.value,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {
        "message": "Property deleted successfully",
        "property_id": property_id
    }


@router.get("/my/listings")
async def get_my_properties(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get current user's property listings (Agent only).
    
    Returns:
        List of user's properties
        
    Raises:
        HTTPException: If user is not an agent
    """
    require_role(current_user, [UserRole.AGENT.value, UserRole.ADMIN.value])
    
    # Get properties
    cursor = db.properties.find({"owner_id": current_user["_id"]}).sort("created_at", -1)
    properties = await cursor.to_list(length=None)
    
    return {
        "total": len(properties),
        "properties": [fix_id(prop) for prop in properties]
    }


@router.post("/{property_id}/favorite")
async def toggle_favorite(
    property_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Toggle property favorite status for current user.
    
    Args:
        property_id: Property ID
        
    Returns:
        Favorite status
    """
    # Validate ObjectId
    if not ObjectId.is_valid(property_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid property ID"
        )
    
    # Check if property exists
    property_doc = await db.properties.find_one({"_id": ObjectId(property_id)})
    if not property_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Check if already favorited
    favorite = await db.favorites.find_one({
        "user_id": current_user["_id"],
        "property_id": ObjectId(property_id)
    })
    
    if favorite:
        # Remove favorite
        await db.favorites.delete_one({"_id": favorite["_id"]})
        await db.properties.update_one(
            {"_id": ObjectId(property_id)},
            {"$inc": {"favorites_count": -1}}
        )
        return {"favorited": False, "message": "Removed from favorites"}
    else:
        # Add favorite
        await db.favorites.insert_one({
            "user_id": current_user["_id"],
            "property_id": ObjectId(property_id),
            "created_at": datetime.utcnow()
        })
        await db.properties.update_one(
            {"_id": ObjectId(property_id)},
            {"$inc": {"favorites_count": 1}}
        )
        return {"favorited": True, "message": "Added to favorites"}
