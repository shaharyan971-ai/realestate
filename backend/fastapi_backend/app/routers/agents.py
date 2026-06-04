"""Agent management routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from bson import ObjectId

from app.config import settings
from app.core.database import get_db
from app.core.security import verify_token, TokenData
from app.services.email_service import EmailService
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agents", tags=["agents"])

email_service = EmailService()


async def get_current_user(token: Optional[str] = None) -> TokenData:
    """Dependency to get current user."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user_data


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_as_agent(
    agent_data: Dict[str, Any],
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Register user as an agent."""
    try:
        user_id = ObjectId(current_user.user_id)
        
        # Check if already an agent
        existing_agent = await db.agents.find_one({"user_id": user_id})
        if existing_agent:
            raise HTTPException(status_code=400, detail="User already registered as agent")
        
        # Create agent record
        agent_doc = {
            "user_id": user_id,
            "agency_name": agent_data.get("agency_name"),
            "agency_logo_url": agent_data.get("agency_logo_url"),
            "license_number": agent_data.get("license_number"),
            "license_expiry": datetime.fromisoformat(agent_data.get("license_expiry")),
            "specialization": agent_data.get("specialization", []),
            "experience_years": agent_data.get("experience_years", 0),
            "verification": {
                "aadhaar_number": agent_data.get("aadhaar_number"),
                "pan_number": agent_data.get("pan_number"),
                "aadhaar_verified": False,
                "pan_verified": False,
                "verified_by_admin": False
            },
            "rating": 0.0,
            "total_reviews": 0,
            "total_properties": 0,
            "total_sales": 0,
            "total_earnings": 0.0,
            "listings_count": 0,
            "listing_limit": 5,  # Default for basic plan
            "commission_rate": 5.0,
            "is_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.agents.insert_one(agent_doc)
        
        # Update user role
        await db.users.update_one(
            {"_id": user_id},
            {"$set": {"role": "agent"}}
        )
        
        # Create agent stats record
        stats_doc = {
            "agent_id": result.inserted_id,
            "total_listings": 0,
            "active_listings": 0,
            "sold_properties": 0,
            "total_views": 0,
            "total_enquiries": 0,
            "conversion_rate": 0.0,
            "avg_response_time_hours": 0.0,
            "customer_satisfaction_score": 0.0,
            "updated_at": datetime.utcnow()
        }
        
        await db.agent_stats.insert_one(stats_doc)
        
        # Send notification to admin
        admin_doc = await db.users.find_one({"role": "admin"})
        if admin_doc:
            notification = {
                "user_id": admin_doc["_id"],
                "notification_type": "admin_alert",
                "title": "New Agent Registration",
                "message": f"New agent registration from {current_user.email}",
                "data": {"agent_id": str(result.inserted_id)},
                "is_read": False,
                "created_at": datetime.utcnow()
            }
            
            await db.notifications.insert_one(notification)
        
        logger.info(f"✅ Agent registered: {result.inserted_id}")
        
        return {
            "status": "success",
            "agent_id": str(result.inserted_id),
            "message": "Agent registration submitted for verification"
        }
    
    except Exception as e:
        logger.error(f"Error registering agent: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{agent_id}")
async def get_agent_profile(
    agent_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """Get agent public profile."""
    try:
        agent = await db.agents.find_one({"_id": ObjectId(agent_id)})
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        user = await db.users.find_one({"_id": agent["user_id"]})
        stats = await db.agent_stats.find_one({"agent_id": ObjectId(agent_id)})
        
        # Get agent's active properties count
        active_properties = await db.properties.count_documents({
            "agent_id": ObjectId(agent_id),
            "status": "available"
        })
        
        return {
            "status": "success",
            "agent": {
                "id": str(agent["_id"]),
                "name": f"{user['first_name']} {user['last_name']}",
                "email": user["email"],
                "phone": user["phone"],
                "profile_picture": user.get("profile_picture_url"),
                "agency_name": agent.get("agency_name"),
                "agency_logo": agent.get("agency_logo_url"),
                "experience_years": agent["experience_years"],
                "specialization": agent.get("specialization", []),
                "rating": agent["rating"],
                "total_reviews": agent["total_reviews"],
                "total_properties": agent["total_properties"],
                "active_listings": active_properties,
                "is_verified": agent["is_verified"],
                "stats": {
                    "total_listings": stats["total_listings"] if stats else 0,
                    "sold_properties": stats["sold_properties"] if stats else 0,
                    "total_views": stats["total_views"] if stats else 0,
                    "customer_satisfaction": stats["customer_satisfaction_score"] if stats else 0.0
                }
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting agent profile: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/agent-info")
async def get_my_agent_info(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user's agent information."""
    try:
        agent = await db.agents.find_one({"user_id": ObjectId(current_user.user_id)})
        if not agent:
            raise HTTPException(status_code=404, detail="You are not registered as an agent")
        
        stats = await db.agent_stats.find_one({"agent_id": agent["_id"]})
        
        return {
            "status": "success",
            "agent": {
                "id": str(agent["_id"]),
                "agency_name": agent.get("agency_name"),
                "license_number": agent["license_number"],
                "listing_limit": agent["listing_limit"],
                "listings_count": agent["listings_count"],
                "available_slots": agent["listing_limit"] - agent["listings_count"],
                "total_earnings": agent["total_earnings"],
                "commission_rate": agent["commission_rate"],
                "is_verified": agent["is_verified"],
                "stats": {
                    "total_listings": stats["total_listings"] if stats else 0,
                    "active_listings": stats["active_listings"] if stats else 0,
                    "sold_properties": stats["sold_properties"] if stats else 0,
                    "total_views": stats["total_views"] if stats else 0,
                    "total_enquiries": stats["total_enquiries"] if stats else 0
                }
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting agent info: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/update-profile")
async def update_agent_profile(
    updates: Dict[str, Any],
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update agent profile."""
    try:
        agent = await db.agents.find_one({"user_id": ObjectId(current_user.user_id)})
        if not agent:
            raise HTTPException(status_code=404, detail="Not an agent")
        
        # Allow only certain fields to be updated
        allowed_updates = {
            "agency_name", "agency_logo_url", "specialization"
        }
        
        update_dict = {
            k: v for k, v in updates.items() if k in allowed_updates
        }
        update_dict["updated_at"] = datetime.utcnow()
        
        await db.agents.update_one(
            {"_id": agent["_id"]},
            {"$set": update_dict}
        )
        
        logger.info(f"Agent profile updated: {agent['_id']}")
        
        return {
            "status": "success",
            "message": "Profile updated successfully"
        }
    
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    verified_only: bool = False,
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """List all agents."""
    try:
        query = {}
        if verified_only:
            query["is_verified"] = True
        
        agents_cursor = db.agents.find(query).skip(skip).limit(limit)
        agents = await agents_cursor.to_list(None)
        total = await db.agents.count_documents(query)
        
        enriched = []
        for agent in agents:
            user = await db.users.find_one({"_id": agent["user_id"]})
            enriched.append({
                "id": str(agent["_id"]),
                "name": f"{user['first_name']} {user['last_name']}",
                "agency_name": agent.get("agency_name"),
                "rating": agent["rating"],
                "experience_years": agent["experience_years"],
                "total_properties": agent["total_properties"],
                "is_verified": agent["is_verified"]
            })
        
        return {
            "status": "success",
            "agents": enriched,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{agent_id}/add-review", status_code=status.HTTP_201_CREATED)
async def add_agent_review(
    agent_id: str,
    rating: int,
    title: str,
    comment: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Add review for an agent."""
    try:
        if not (1 <= rating <= 5):
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        review_doc = {
            "agent_id": ObjectId(agent_id),
            "reviewer_id": ObjectId(current_user.user_id),
            "rating": rating,
            "title": title,
            "comment": comment,
            "helpful_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.reviews.insert_one(review_doc)
        
        # Update agent rating
        all_reviews = await db.reviews.find({"agent_id": ObjectId(agent_id)}).to_list(None)
        avg_rating = sum(r["rating"] for r in all_reviews) / len(all_reviews)
        
        await db.agents.update_one(
            {"_id": ObjectId(agent_id)},
            {
                "$set": {
                    "rating": round(avg_rating, 1),
                    "total_reviews": len(all_reviews)
                }
            }
        )
        
        logger.info(f"Review added for agent {agent_id}")
        
        return {
            "status": "success",
            "review_id": str(result.inserted_id),
            "message": "Review added successfully"
        }
    
    except Exception as e:
        logger.error(f"Error adding review: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{agent_id}/reviews")
async def get_agent_reviews(
    agent_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """Get agent reviews."""
    try:
        reviews_cursor = db.reviews.find({"agent_id": ObjectId(agent_id)}).skip(skip).limit(limit)
        reviews = await reviews_cursor.to_list(None)
        total = await db.reviews.count_documents({"agent_id": ObjectId(agent_id)})
        
        enriched = []
        for review in reviews:
            reviewer = await db.users.find_one({"_id": review["reviewer_id"]})
            enriched.append({
                "id": str(review["_id"]),
                "reviewer_name": f"{reviewer['first_name']} {reviewer['last_name']}" if reviewer else "Anonymous",
                "rating": review["rating"],
                "title": review["title"],
                "comment": review["comment"],
                "helpful_count": review.get("helpful_count", 0),
                "created_at": review["created_at"].isoformat()
            })
        
        return {
            "status": "success",
            "reviews": enriched,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    except Exception as e:
        logger.error(f"Error fetching reviews: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{agent_id}/earnings")
async def get_agent_earnings(
    agent_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get agent earnings dashboard."""
    try:
        agent = await db.agents.find_one({"_id": ObjectId(agent_id)})
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check authorization
        if agent["user_id"] != ObjectId(current_user.user_id):
            user = await db.users.find_one({"_id": ObjectId(current_user.user_id)})
            if user.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Get transactions
        transactions = await db.transactions.find({
            "agent_id": ObjectId(agent_id)
        }).to_list(None)
        
        total_earnings = sum(
            t["amount"] for t in transactions 
            if t.get("transaction_type") == "commission"
        )
        
        monthly_earnings = {}
        for t in transactions:
            month_key = t["created_at"].strftime("%Y-%m")
            if month_key not in monthly_earnings:
                monthly_earnings[month_key] = 0
            monthly_earnings[month_key] += t["amount"]
        
        return {
            "status": "success",
            "earnings": {
                "total": total_earnings,
                "monthly": monthly_earnings,
                "pending": agent.get("total_earnings", 0),
                "commission_rate": agent["commission_rate"]
            }
        }
    
    except Exception as e:
        logger.error(f"Error fetching earnings: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{agent_id}/verify", status_code=status.HTTP_200_OK)
async def verify_agent(
    agent_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Verify agent (Admin only)."""
    try:
        user = await db.users.find_one({"_id": ObjectId(current_user.user_id)})
        if not user or user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        agent = await db.agents.find_one({"_id": ObjectId(agent_id)})
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update agent verification
        await db.agents.update_one(
            {"_id": ObjectId(agent_id)},
            {
                "$set": {
                    "is_verified": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Send verification email
        agent_user = await db.users.find_one({"_id": agent["user_id"]})
        await email_service.send_agent_verification_email(
            to_email=agent_user["email"],
            agent_name=agent_user["first_name"]
        )
        
        logger.info(f"Agent verified: {agent_id}")
        
        return {
            "status": "success",
            "message": "Agent verified successfully"
        }
    
    except Exception as e:
        logger.error(f"Error verifying agent: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
