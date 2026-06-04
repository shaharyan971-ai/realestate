"""Booking service for managing property bookings."""
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
import logging

from app.core.database import get_db
from app.models import BookingModel, BookingStatus, PaymentStatus
from app.config import settings

logger = logging.getLogger(__name__)


class BookingService:
    """Service for booking operations."""
    
    def __init__(self, db):
        self.db = db
    
    async def create_booking(
        self,
        property_id: str,
        buyer_id: str,
        visit_date: datetime,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new property booking.
        
        Args:
            property_id: Property ID
            buyer_id: Buyer user ID
            visit_date: Scheduled visit date
            notes: Optional booking notes
            
        Returns:
            Created booking
            
        Raises:
            ValueError: If property not found or not available
        """
        # Validate property exists and is active
        property_doc = await self.db.properties.find_one({
            "_id": ObjectId(property_id),
            "status": "active"
        })
        
        if not property_doc:
            raise ValueError("Property not found or not available")
        
        # Get agent ID
        agent_id = property_doc.get("agent_id") or property_doc.get("owner_id")
        
        # Create booking
        booking = {
            "property_id": ObjectId(property_id),
            "buyer_id": ObjectId(buyer_id),
            "agent_id": agent_id,
            "status": BookingStatus.PENDING.value,
            "visit_date": visit_date,
            "notes": notes,
            "amount": settings.BOOKING_FEE_AMOUNT,
            "payment_status": PaymentStatus.PENDING.value,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.db.bookings.insert_one(booking)
        booking["_id"] = result.inserted_id
        
        # Increment booking count on property
        await self.db.properties.update_one(
            {"_id": ObjectId(property_id)},
            {"$inc": {"booking_count": 1}}
        )
        
        logger.info(f"✅ Booking created: {result.inserted_id}")
        return booking
    
    async def confirm_booking(self, booking_id: str, payment_id: str) -> Dict[str, Any]:
        """
        Confirm booking after successful payment.
        
        Args:
            booking_id: Booking ID
            payment_id: Payment ID
            
        Returns:
            Updated booking
        """
        result = await self.db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {
                "$set": {
                    "status": BookingStatus.CONFIRMED.value,
                    "payment_status": PaymentStatus.COMPLETED.value,
                    "payment_id": ObjectId(payment_id),
                    "confirmed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise ValueError("Booking not found")
        
        booking = await self.db.bookings.find_one({"_id": ObjectId(booking_id)})
        logger.info(f"✅ Booking confirmed: {booking_id}")
        
        return booking
    
    async def cancel_booking(self, booking_id: str, user_id: str) -> Dict[str, Any]:
        """
        Cancel a booking.
        
        Args:
            booking_id: Booking ID
            user_id: User requesting cancellation
            
        Returns:
            Updated booking
        """
        # Get booking
        booking = await self.db.bookings.find_one({"_id": ObjectId(booking_id)})
        
        if not booking:
            raise ValueError("Booking not found")
        
        # Check if user is authorized (buyer or agent)
        if str(booking["buyer_id"]) != user_id and str(booking.get("agent_id")) != user_id:
            raise PermissionError("Not authorized to cancel this booking")
        
        # Update booking status
        await self.db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {
                "$set": {
                    "status": BookingStatus.CANCELLED.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"✅ Booking cancelled: {booking_id}")
        
        # TODO: Process refund if payment was made
        
        return booking
    
    async def get_user_bookings(self, user_id: str) -> list:
        """
        Get all bookings for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of bookings
        """
        cursor = self.db.bookings.find({"buyer_id": ObjectId(user_id)}).sort("created_at", -1)
        bookings = await cursor.to_list(length=None)
        
        return bookings
    
    async def get_agent_bookings(self, agent_id: str) -> list:
        """
        Get all bookings for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            List of bookings
        """
        cursor = self.db.bookings.find({"agent_id": ObjectId(agent_id)}).sort("created_at", -1)
        bookings = await cursor.to_list(length=None)
        
        return bookings


async def get_booking_service(db=None):
    """Get booking service instance."""
    if db is None:
        db = get_db()
    return BookingService(db)
