"""Database connection and utilities."""
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Global database instance
_db_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def connect_db() -> None:
    """Connect to MongoDB."""
    global _db_client, _db
    
    try:
        logger.info(f"Attempting to connect to MongoDB at: {settings.MONGODB_URL}")
        _db_client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000  # 5 second timeout
        )
        _db = _db_client[settings.MONGODB_DB_NAME]
        
        # Ping to verify connection
        await _db_client.admin.command('ping')
        logger.info(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")
    except Exception as e:
        logger.warning(f"⚠️  MongoDB connection failed: {e}")
        logger.warning("Server will start but database operations will fail")
        # Don't raise - allow server to start without MongoDB


async def close_db() -> None:
    """Close MongoDB connection."""
    global _db_client
    if _db_client:
        _db_client.close()
        logger.info("MongoDB connection closed")


def get_db() -> AsyncDatabase:
    """Get database instance."""
    if _db is None:
        raise RuntimeError("Database not connected. Call connect_db() first.")
    return _db


# Collection helpers
async def get_collection(collection_name: str):
    """Get specific collection."""
    db = get_db()
    return db[collection_name]


# Index creation
async def create_indexes() -> None:
    """Create database indexes for performance."""
    db = get_db()
    
    try:
        # Users
        await db.users.create_index("email", unique=True)
        await db.users.create_index("created_at")
        
        # Properties
        await db.properties.create_index("owner_id")
        await db.properties.create_index("city")
        await db.properties.create_index([("latitude", "2dsphere"), ("longitude", "2dsphere")])
        await db.properties.create_index("created_at")
        await db.properties.create_index("is_featured")
        
        # Bookings
        await db.bookings.create_index("property_id")
        await db.bookings.create_index("buyer_id")
        await db.bookings.create_index("payment_status")
        
        # Payments
        await db.payments.create_index("user_id")
        await db.payments.create_index("created_at")
        await db.payments.create_index("stripe_payment_id")
        await db.payments.create_index("razorpay_payment_id")
        
        # Subscriptions
        await db.subscriptions.create_index("user_id")
        await db.subscriptions.create_index("status")
        await db.subscriptions.create_index("active_until")
        
        # Favorites
        await db.favorites.create_index([("user_id", 1), ("property_id", 1)], unique=True)
        
        # Reviews
        await db.reviews.create_index("agent_id")
        await db.reviews.create_index("property_id")
        await db.reviews.create_index("created_at")
        
        # Notifications
        await db.notifications.create_index("user_id")
        await db.notifications.create_index("is_read")
        
        logger.info("✅ Database indexes created")
    except Exception as e:
        logger.error(f"❌ Error creating indexes: {e}")
        raise
