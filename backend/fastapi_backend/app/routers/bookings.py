"""Booking management routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from bson import ObjectId

from app.config import settings
from app.core.database import get_db
from app.core.security import verify_token, TokenData
from app.schemas.models import (
    BookingStatus, CreateBookingRequest, PaymentStatus
)
from app.services.email_service import EmailService
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/bookings", tags=["bookings"])

email_service = EmailService()


async def get_current_user(token: Optional[str] = None) -> TokenData:
    """Dependency to get current user."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user_data


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_booking(
    request: CreateBookingRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new booking."""
    try:
        property_id = ObjectId(request.property_id)
        buyer_id = ObjectId(current_user.user_id)
        
        # Get property details
        prop = await db.properties.find_one({"_id": property_id})
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")
        
        if prop["status"] != "available":
            raise HTTPException(status_code=400, detail="Property is not available")
        
        # Get seller/agent details
        seller_id = prop["owner_id"]
        agent_id = prop.get("agent_id") or seller_id
        
        # Create booking record
        booking_doc = {
            "property_id": property_id,
            "buyer_id": buyer_id,
            "agent_id": agent_id,
            "seller_id": seller_id,
            "visit_date": request.visit_date,
            "notes": request.notes or "",
            "status": BookingStatus.PENDING.value,
            "payment_status": PaymentStatus.PENDING.value,
            "amount": settings.BOOKING_FEE_AMOUNT / 100,  # Convert paise to rupees
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.bookings.insert_one(booking_doc)
        
        # Update property booking count
        await db.properties.update_one(
            {"_id": property_id},
            {"$inc": {"bookings_count": 1}}
        )
        
        # Create notification for agent
        notification = {
            "user_id": agent_id,
            "notification_type": "new_booking",
            "title": "New Booking Request",
            "message": f"New booking request for {prop['title']}",
            "data": {
                "booking_id": str(result.inserted_id),
                "property_id": str(property_id)
            },
            "action_url": f"/bookings/{str(result.inserted_id)}",
            "is_read": False,
            "created_at": datetime.utcnow()
        }
        
        await db.notifications.insert_one(notification)
        
        logger.info(f"✅ Booking created: {result.inserted_id}")
        
        return {
            "status": "success",
            "booking_id": str(result.inserted_id),
            "amount": booking_doc["amount"],
            "message": "Booking created. Please proceed to payment."
        }
    
    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{booking_id}")
async def get_booking(
    booking_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get booking details."""
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Check authorization (buyer, agent, or admin)
        if (booking["buyer_id"] != ObjectId(current_user.user_id) and 
            booking["agent_id"] != ObjectId(current_user.user_id)):
            user = await db.users.find_one({"_id": ObjectId(current_user.user_id)})
            if user.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Get related data
        prop = await db.properties.find_one({"_id": booking["property_id"]})
        buyer = await db.users.find_one({"_id": booking["buyer_id"]})
        agent = await db.users.find_one({"_id": booking["agent_id"]})
        
        return {
            "status": "success",
            "booking": {
                "id": str(booking["_id"]),
                "property": {
                    "id": str(prop["_id"]),
                    "title": prop["title"],
                    "price": prop["price"],
                    "image_url": prop.get("media", {}).get("image_urls", [None])[0]
                },
                "buyer": {
                    "id": str(buyer["_id"]),
                    "name": f"{buyer['first_name']} {buyer['last_name']}",
                    "email": buyer["email"],
                    "phone": buyer["phone"]
                },
                "agent": {
                    "id": str(agent["_id"]),
                    "name": f"{agent['first_name']} {agent['last_name']}",
                    "phone": agent["phone"]
                },
                "visit_date": booking["visit_date"].isoformat(),
                "notes": booking.get("notes", ""),
                "status": booking["status"],
                "payment_status": booking["payment_status"],
                "amount": booking["amount"],
                "created_at": booking["created_at"].isoformat()
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting booking: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/my-bookings")
async def get_my_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    status_filter: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user's bookings."""
    try:
        user_id = ObjectId(current_user.user_id)
        
        # Build query
        query = {
            "$or": [
                {"buyer_id": user_id},
                {"agent_id": user_id}
            ]
        }
        
        if status_filter:
            query["status"] = status_filter
        
        # Get bookings
        bookings_cursor = db.bookings.find(query).skip(skip).limit(limit)
        bookings = await bookings_cursor.to_list(None)
        
        # Get total count
        total = await db.bookings.count_documents(query)
        
        # Enrich booking data
        enriched_bookings = []
        for booking in bookings:
            prop = await db.properties.find_one({"_id": booking["property_id"]})
            enriched_bookings.append({
                "id": str(booking["_id"]),
                "property_title": prop["title"] if prop else "Unknown",
                "property_image": prop.get("media", {}).get("image_urls", [None])[0] if prop else None,
                "visit_date": booking["visit_date"].isoformat(),
                "status": booking["status"],
                "payment_status": booking["payment_status"],
                "amount": booking["amount"],
                "created_at": booking["created_at"].isoformat()
            })
        
        return {
            "status": "success",
            "bookings": enriched_bookings,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    except Exception as e:
        logger.error(f"Error fetching bookings: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{booking_id}/confirm")
async def confirm_booking(
    booking_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Confirm booking (agent only)."""
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Check authorization
        if booking["agent_id"] != ObjectId(current_user.user_id):
            user = await db.users.find_one({"_id": ObjectId(current_user.user_id)})
            if user.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Only agent can confirm")
        
        # Update booking status
        await db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {
                "$set": {
                    "status": BookingStatus.CONFIRMED.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Send notification to buyer
        buyer = await db.users.find_one({"_id": booking["buyer_id"]})
        notification = {
            "user_id": booking["buyer_id"],
            "notification_type": "booking_confirmed",
            "title": "Booking Confirmed",
            "message": "Your booking has been confirmed by the agent",
            "data": {"booking_id": booking_id},
            "is_read": False,
            "created_at": datetime.utcnow()
        }
        
        await db.notifications.insert_one(notification)
        
        # Send confirmation email
        prop = await db.properties.find_one({"_id": booking["property_id"]})
        await email_service.send_booking_confirmation(
            to_email=buyer["email"],
            customer_name=buyer["first_name"],
            property_title=prop["title"] if prop else "Your Property",
            visit_date=booking["visit_date"],
            booking_id=booking_id
        )
        
        logger.info(f"Booking confirmed: {booking_id}")
        
        return {
            "status": "success",
            "message": "Booking confirmed"
        }
    
    except Exception as e:
        logger.error(f"Error confirming booking: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{booking_id}/complete")
async def complete_booking(
    booking_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Mark booking as completed."""
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Check authorization (agent, buyer, or admin)
        user_id = ObjectId(current_user.user_id)
        user = await db.users.find_one({"_id": user_id})
        
        if (booking["agent_id"] != user_id and booking["buyer_id"] != user_id):
            if user.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Update booking status
        await db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {
                "$set": {
                    "status": BookingStatus.COMPLETED.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Booking completed: {booking_id}")
        
        return {
            "status": "success",
            "message": "Booking completed"
        }
    
    except Exception as e:
        logger.error(f"Error completing booking: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str,
    reason: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Cancel booking with refund."""
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Check authorization
        user_id = ObjectId(current_user.user_id)
        if booking["buyer_id"] != user_id:
            user = await db.users.find_one({"_id": user_id})
            if user.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Only buyer can cancel")
        
        # Update booking
        await db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {
                "$set": {
                    "status": BookingStatus.CANCELLED.value,
                    "cancelled_reason": reason,
                    "cancelled_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Create refund if payment was made
        if booking["payment_status"] == PaymentStatus.COMPLETED.value:
            refund_doc = {
                "booking_id": ObjectId(booking_id),
                "user_id": booking["buyer_id"],
                "amount": booking["amount"],
                "reason": f"Booking cancellation: {reason}",
                "status": PaymentStatus.PROCESSING.value,
                "created_at": datetime.utcnow()
            }
            
            await db.refunds.insert_one(refund_doc)
            
            # Update booking payment status
            await db.bookings.update_one(
                {"_id": ObjectId(booking_id)},
                {"$set": {"payment_status": PaymentStatus.REFUNDED.value}}
            )
        
        logger.info(f"Booking cancelled: {booking_id}")
        
        return {
            "status": "success",
            "message": "Booking cancelled"
        }
    
    except Exception as e:
        logger.error(f"Error cancelling booking: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{booking_id}/reschedule")
async def reschedule_booking(
    booking_id: str,
    new_date: datetime,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Reschedule booking to new date."""
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Check authorization
        user_id = ObjectId(current_user.user_id)
        if (booking["buyer_id"] != user_id and booking["agent_id"] != user_id):
            user = await db.users.find_one({"_id": user_id})
            if user.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Update visit date
        await db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {
                "$set": {
                    "visit_date": new_date,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Booking rescheduled: {booking_id}")
        
        return {
            "status": "success",
            "message": "Booking rescheduled",
            "new_date": new_date.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error rescheduling booking: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/property/{property_id}/bookings")
async def get_property_bookings(
    property_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all bookings for a property (owner/agent only)."""
    try:
        prop = await db.properties.find_one({"_id": ObjectId(property_id)})
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Check authorization
        user_id = ObjectId(current_user.user_id)
        user = await db.users.find_one({"_id": user_id})
        
        if (prop["owner_id"] != user_id and (not prop.get("agent_id") or prop["agent_id"] != user_id)):
            if user.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Get bookings
        bookings = await db.bookings.find({
            "property_id": ObjectId(property_id)
        }).to_list(None)
        
        enriched = []
        for booking in bookings:
            buyer = await db.users.find_one({"_id": booking["buyer_id"]})
            enriched.append({
                "id": str(booking["_id"]),
                "buyer_name": f"{buyer['first_name']} {buyer['last_name']}" if buyer else "Unknown",
                "buyer_phone": buyer["phone"] if buyer else "",
                "visit_date": booking["visit_date"].isoformat(),
                "status": booking["status"],
                "payment_status": booking["payment_status"],
                "amount": booking["amount"],
                "created_at": booking["created_at"].isoformat()
            })
        
        return {
            "status": "success",
            "bookings": enriched,
            "total": len(enriched)
        }
    
    except Exception as e:
        logger.error(f"Error fetching property bookings: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
