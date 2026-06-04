"""Subscription service for managing user subscriptions."""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from bson import ObjectId
import logging

from app.core.database import get_db
from app.models import SubscriptionModel, SubscriptionStatus, SubscriptionPlan
from app.services.payment_service import SUBSCRIPTION_PLANS
from app.config import settings

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for subscription operations."""
    
    def __init__(self, db):
        self.db = db
    
    async def create_subscription(
        self,
        user_id: str,
        plan: str,
        billing_cycle: str = "monthly",
        payment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new subscription.
        
        Args:
            user_id: User ID
            plan: Subscription plan (basic, pro, enterprise)
            billing_cycle: Billing cycle (monthly, yearly)
            payment_id: Payment ID if already paid
            
        Returns:
            Created subscription
        """
        # Get plan details
        plan_details = SUBSCRIPTION_PLANS.get(plan)
        if not plan_details:
            raise ValueError(f"Invalid plan: {plan}")
        
        # Calculate active_until date
        if billing_cycle == "monthly":
            active_until = datetime.utcnow() + timedelta(days=30)
        elif billing_cycle == "yearly":
            active_until = datetime.utcnow() + timedelta(days=365)
        else:
            raise ValueError(f"Invalid billing cycle: {billing_cycle}")
        
        # Check if user already has active subscription
        existing = await self.db.subscriptions.find_one({
            "user_id": ObjectId(user_id),
            "status": SubscriptionStatus.ACTIVE.value
        })
        
        if existing:
            # Cancel existing subscription
            await self.cancel_subscription(str(existing["_id"]))
        
        # Create subscription
        subscription = {
            "user_id": ObjectId(user_id),
            "plan": plan,
            "status": SubscriptionStatus.PENDING.value if not payment_id else SubscriptionStatus.ACTIVE.value,
            "amount": plan_details["amount"],
            "currency": plan_details["currency"],
            "billing_cycle": billing_cycle,
            "started_at": datetime.utcnow() if payment_id else None,
            "active_until": active_until,
            "max_listings": plan_details["max_listings"],
            "features": plan_details["features"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.db.subscriptions.insert_one(subscription)
        subscription["_id"] = result.inserted_id
        
        logger.info(f"✅ Subscription created: {result.inserted_id} for user {user_id}")
        return subscription
    
    async def activate_subscription(self, subscription_id: str, payment_id: str) -> Dict[str, Any]:
        """
        Activate subscription after successful payment.
        
        Args:
            subscription_id: Subscription ID
            payment_id: Payment ID
            
        Returns:
            Updated subscription
        """
        result = await self.db.subscriptions.update_one(
            {"_id": ObjectId(subscription_id)},
            {
                "$set": {
                    "status": SubscriptionStatus.ACTIVE.value,
                    "started_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise ValueError("Subscription not found")
        
        subscription = await self.db.subscriptions.find_one({"_id": ObjectId(subscription_id)})
        logger.info(f"✅ Subscription activated: {subscription_id}")
        
        return subscription
    
    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            Updated subscription
        """
        result = await self.db.subscriptions.update_one(
            {"_id": ObjectId(subscription_id)},
            {
                "$set": {
                    "status": SubscriptionStatus.CANCELLED.value,
                    "cancelled_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise ValueError("Subscription not found")
        
        subscription = await self.db.subscriptions.find_one({"_id": ObjectId(subscription_id)})
        logger.info(f"✅ Subscription cancelled: {subscription_id}")
        
        return subscription
    
    async def renew_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Renew an expired subscription.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            Updated subscription
        """
        subscription = await self.db.subscriptions.find_one({"_id": ObjectId(subscription_id)})
        
        if not subscription:
            raise ValueError("Subscription not found")
        
        # Calculate new active_until date
        billing_cycle = subscription.get("billing_cycle", "monthly")
        if billing_cycle == "monthly":
            new_active_until = datetime.utcnow() + timedelta(days=30)
        else:
            new_active_until = datetime.utcnow() + timedelta(days=365)
        
        # Update subscription
        result = await self.db.subscriptions.update_one(
            {"_id": ObjectId(subscription_id)},
            {
                "$set": {
                    "status": SubscriptionStatus.ACTIVE.value,
                    "active_until": new_active_until,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"✅ Subscription renewed: {subscription_id}")
        
        return await self.db.subscriptions.find_one({"_id": ObjectId(subscription_id)})
    
    async def get_user_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's active subscription.
        
        Args:
            user_id: User ID
            
        Returns:
            Active subscription or None
        """
        subscription = await self.db.subscriptions.find_one({
            "user_id": ObjectId(user_id),
            "status": SubscriptionStatus.ACTIVE.value
        })
        
        return subscription
    
    async def check_subscription_limits(self, user_id: str, feature: str) -> bool:
        """
        Check if user can access a feature based on subscription.
        
        Args:
            user_id: User ID
            feature: Feature to check
            
        Returns:
            True if user can access feature
        """
        subscription = await self.get_user_subscription(user_id)
        
        if not subscription:
            # No active subscription, use basic limits
            return False
        
        # Check if subscription is still valid
        if subscription["active_until"] < datetime.utcnow():
            # Subscription expired
            await self.db.subscriptions.update_one(
                {"_id": subscription["_id"]},
                {"$set": {"status": SubscriptionStatus.EXPIRED.value}}
            )
            return False
        
        # Check feature access
        features = subscription.get("features", [])
        return feature in features
    
    async def get_listing_limit(self, user_id: str) -> int:
        """
        Get user's listing limit based on subscription.
        
        Args:
            user_id: User ID
            
        Returns:
            Maximum number of listings allowed
        """
        subscription = await self.get_user_subscription(user_id)
        
        if not subscription:
            return 1  # Default limit for non-subscribers
        
        return subscription.get("max_listings", 1)


async def get_subscription_service(db=None):
    """Get subscription service instance."""
    if db is None:
        db = get_db()
    return SubscriptionService(db)
