"""Subscription management routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
from bson import ObjectId

from app.config import settings
from app.core.database import get_db
from app.core.security import verify_token, TokenData
from app.schemas.models import (
    SubscriptionSchema, SubscriptionStatus, SubscriptionPlanEnum,
    CreateSubscriptionRequest, PaymentMethod, PaymentStatus
)
from app.services.payment_service import StripeService, RazorpayService
from app.services.email_service import EmailService
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

stripe_service = StripeService()
razorpay_service = RazorpayService()
email_service = EmailService()


async def get_current_user(token: Optional[str] = None) -> TokenData:
    """Dependency to get current user."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user_data


# ==================== SUBSCRIPTION PLANS ====================

@router.get("/plans")
async def get_subscription_plans(db: AsyncIOMotorDatabase = Depends(get_db)) -> Dict[str, Any]:
    """Get all available subscription plans."""
    try:
        plans = await db.subscription_plans.find({}).to_list(None)
        
        return {
            "status": "success",
            "plans": [
                {
                    "id": str(plan["_id"]),
                    "plan_key": plan["plan_key"],
                    "name": plan["name"],
                    "description": plan["description"],
                    "price": plan["price"],
                    "currency": plan["currency"],
                    "billing_cycle": plan["billing_cycle"],
                    "features": plan["features"],
                    "listing_limit": plan.get("listing_limit", 5),
                    "featured_listings": plan.get("featured_listings", 0),
                    "priority_search": plan.get("priority_search", False),
                    "analytics_access": plan.get("analytics_access", False)
                }
                for plan in plans
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching plans: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plans", status_code=status.HTTP_201_CREATED)
async def create_subscription_plan(
    plan: Dict[str, Any],
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create new subscription plan (Admin only)."""
    try:
        # Verify admin role
        user = await db.users.find_one({"_id": ObjectId(current_user.user_id)})
        if not user or user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        plan_doc = {
            **plan,
            "created_at": datetime.utcnow()
        }
        
        result = await db.subscription_plans.insert_one(plan_doc)
        
        return {
            "status": "success",
            "plan_id": str(result.inserted_id),
            "message": "Subscription plan created"
        }
    except Exception as e:
        logger.error(f"Error creating plan: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== USER SUBSCRIPTIONS ====================

@router.post("/subscribe")
async def subscribe_to_plan(
    request: CreateSubscriptionRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Subscribe user to a plan."""
    try:
        user_id = ObjectId(current_user.user_id)
        
        # Check if user already has active subscription
        existing_sub = await db.subscriptions.find_one({
            "user_id": user_id,
            "status": SubscriptionStatus.ACTIVE.value
        })
        
        if existing_sub:
            raise HTTPException(
                status_code=400,
                detail="User already has an active subscription"
            )
        
        # Get plan details
        plan = await db.subscription_plans.find_one({
            "plan_key": request.plan_id.value
        })
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Get user details
        user = await db.users.find_one({"_id": user_id})
        
        # Create subscription based on payment method
        if request.payment_method == PaymentMethod.STRIPE:
            return await create_stripe_subscription(
                db, user, plan, current_user, request.plan_id
            )
        elif request.payment_method == PaymentMethod.RAZORPAY:
            return await create_razorpay_subscription(
                db, user, plan, current_user, request.plan_id
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid payment method")
    
    except Exception as e:
        logger.error(f"Error subscribing: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


async def create_stripe_subscription(
    db, user: Dict[str, Any], plan: Dict[str, Any],
    current_user: TokenData, plan_id: SubscriptionPlanEnum
) -> Dict[str, Any]:
    """Create Stripe subscription."""
    try:
        subscription = await stripe_service.create_subscription(
            customer_email=user["email"],
            plan_id=plan["stripe_plan_id"],
            metadata={
                "user_id": str(current_user.user_id),
                "plan": plan_id.value
            }
        )
        
        # Store subscription in database
        now = datetime.utcnow()
        sub_doc = {
            "user_id": ObjectId(current_user.user_id),
            "plan_id": plan_id.value,
            "status": SubscriptionStatus.ACTIVE.value,
            "stripe_subscription_id": subscription["subscription_id"],
            "start_date": now,
            "current_period_start": now,
            "current_period_end": datetime.fromtimestamp(subscription["current_period_end"]),
            "active_until": datetime.fromtimestamp(subscription["current_period_end"]),
            "payment_method": PaymentMethod.STRIPE.value,
            "auto_renew": True,
            "created_at": now,
            "updated_at": now
        }
        
        result = await db.subscriptions.insert_one(sub_doc)
        
        # Update user's listing limit
        await db.users.update_one(
            {"_id": ObjectId(current_user.user_id)},
            {"$set": {"subscription_plan": plan_id.value}}
        )
        
        # Send confirmation email
        await email_service.send_subscription_confirmation(
            to_email=user["email"],
            customer_name=user["first_name"],
            plan_name=plan["name"],
            amount=plan["price"],
            currency=plan["currency"]
        )
        
        logger.info(f"✅ Stripe subscription created: {subscription['subscription_id']}")
        
        return {
            "status": "success",
            "subscription_id": str(result.inserted_id),
            "stripe_subscription_id": subscription["subscription_id"],
            "message": "Subscription activated"
        }
    
    except Exception as e:
        logger.error(f"Error creating Stripe subscription: {str(e)}")
        raise


async def create_razorpay_subscription(
    db, user: Dict[str, Any], plan: Dict[str, Any],
    current_user: TokenData, plan_id: SubscriptionPlanEnum
) -> Dict[str, Any]:
    """Create Razorpay subscription."""
    try:
        subscription = await razorpay_service.create_subscription(
            plan_id=plan["razorpay_plan_id"],
            metadata={
                "user_id": str(current_user.user_id),
                "plan": plan_id.value
            }
        )
        
        # Store subscription in database
        now = datetime.utcnow()
        sub_doc = {
            "user_id": ObjectId(current_user.user_id),
            "plan_id": plan_id.value,
            "status": SubscriptionStatus.ACTIVE.value,
            "razorpay_subscription_id": subscription["id"],
            "start_date": now,
            "current_period_start": now,
            "current_period_end": now + timedelta(days=30),
            "active_until": now + timedelta(days=30),
            "payment_method": PaymentMethod.RAZORPAY.value,
            "auto_renew": True,
            "created_at": now,
            "updated_at": now
        }
        
        result = await db.subscriptions.insert_one(sub_doc)
        
        # Update user's subscription plan
        await db.users.update_one(
            {"_id": ObjectId(current_user.user_id)},
            {"$set": {"subscription_plan": plan_id.value}}
        )
        
        # Send confirmation email
        await email_service.send_subscription_confirmation(
            to_email=user["email"],
            customer_name=user["first_name"],
            plan_name=plan["name"],
            amount=plan["price"],
            currency=plan["currency"]
        )
        
        logger.info(f"✅ Razorpay subscription created: {subscription['id']}")
        
        return {
            "status": "success",
            "subscription_id": str(result.inserted_id),
            "razorpay_subscription_id": subscription["id"],
            "amount": subscription["plan_id"],
            "message": "Subscription activated"
        }
    
    except Exception as e:
        logger.error(f"Error creating Razorpay subscription: {str(e)}")
        raise


@router.get("/my-subscription")
async def get_my_subscription(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user's active subscription."""
    try:
        subscription = await db.subscriptions.find_one({
            "user_id": ObjectId(current_user.user_id),
            "status": {"$in": [SubscriptionStatus.ACTIVE.value, SubscriptionStatus.SUSPENDED.value]}
        })
        
        if not subscription:
            return {
                "status": "success",
                "subscription": None,
                "message": "No active subscription"
            }
        
        # Get plan details
        plan = await db.subscription_plans.find_one({
            "plan_key": subscription["plan_id"]
        })
        
        return {
            "status": "success",
            "subscription": {
                "id": str(subscription["_id"]),
                "plan_id": subscription["plan_id"],
                "plan_name": plan["name"] if plan else "",
                "status": subscription["status"],
                "active_until": subscription["active_until"].isoformat(),
                "auto_renew": subscription.get("auto_renew", True),
                "created_at": subscription["created_at"].isoformat()
            }
        }
    
    except Exception as e:
        logger.error(f"Error fetching subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cancel")
async def cancel_subscription(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Cancel current subscription."""
    try:
        subscription = await db.subscriptions.find_one({
            "user_id": ObjectId(current_user.user_id),
            "status": SubscriptionStatus.ACTIVE.value
        })
        
        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        # Update subscription status
        await db.subscriptions.update_one(
            {"_id": subscription["_id"]},
            {
                "$set": {
                    "status": SubscriptionStatus.CANCELLED.value,
                    "cancelled_at": datetime.utcnow(),
                    "auto_renew": False,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Subscription cancelled: {subscription['_id']}")
        
        return {
            "status": "success",
            "message": "Subscription cancelled"
        }
    
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upgrade")
async def upgrade_subscription(
    new_plan_id: SubscriptionPlanEnum,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Upgrade to higher plan."""
    try:
        current_sub = await db.subscriptions.find_one({
            "user_id": ObjectId(current_user.user_id),
            "status": SubscriptionStatus.ACTIVE.value
        })
        
        if not current_sub:
            raise HTTPException(status_code=404, detail="No active subscription")
        
        # Get new plan
        new_plan = await db.subscription_plans.find_one({
            "plan_key": new_plan_id.value
        })
        
        if not new_plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Update subscription plan
        await db.subscriptions.update_one(
            {"_id": current_sub["_id"]},
            {
                "$set": {
                    "plan_id": new_plan_id.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Subscription upgraded to {new_plan_id.value}")
        
        return {
            "status": "success",
            "message": f"Upgraded to {new_plan['name']} plan"
        }
    
    except Exception as e:
        logger.error(f"Error upgrading subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== SUBSCRIPTION EXPIRY MANAGEMENT ====================

@router.get("/check-expiry")
async def check_subscription_expiry(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Check subscription expiry status."""
    try:
        subscription = await db.subscriptions.find_one({
            "user_id": ObjectId(current_user.user_id),
            "status": SubscriptionStatus.ACTIVE.value
        })
        
        if not subscription:
            return {
                "status": "success",
                "expiring_soon": False,
                "days_remaining": 0
            }
        
        now = datetime.utcnow()
        days_remaining = (subscription["active_until"] - now).days
        
        return {
            "status": "success",
            "expiring_soon": days_remaining <= 7,
            "days_remaining": days_remaining,
            "expiry_date": subscription["active_until"].isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error checking expiry: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/renew")
async def renew_subscription(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Manually renew subscription."""
    try:
        subscription = await db.subscriptions.find_one({
            "user_id": ObjectId(current_user.user_id)
        })
        
        if not subscription:
            raise HTTPException(status_code=404, detail="No subscription found")
        
        # Calculate new expiry date
        new_expiry = datetime.utcnow() + timedelta(days=30)
        
        # Update subscription
        await db.subscriptions.update_one(
            {"_id": subscription["_id"]},
            {
                "$set": {
                    "status": SubscriptionStatus.ACTIVE.value,
                    "active_until": new_expiry,
                    "renewal_reminder_sent": False,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Subscription renewed: {subscription['_id']}")
        
        return {
            "status": "success",
            "message": "Subscription renewed",
            "new_expiry": new_expiry.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error renewing subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
