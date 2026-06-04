"""Payment routes for Stripe and Razorpay."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.config import settings
from app.core.database import get_db
from app.core.security import verify_token, TokenData
from app.schemas.models import (
    CreatePaymentRequest, PaymentSchema, PaymentStatus, PaymentMethod,
    BookingSchema, SubscriptionSchema, PaymentWebhookRequest
)
from app.services.payment_service import StripeService, RazorpayService
from app.services.email_service import EmailService
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payments", tags=["payments"])

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


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CreatePaymentRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a Stripe checkout session.
    
    Returns session ID for Stripe Checkout.
    """
    try:
        # Get user details from database
        user = await db.users.find_one({"_id": current_user.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare metadata
        metadata = {
            "user_id": str(current_user.user_id),
            "payment_type": request.payment_type,
            "booking_id": request.booking_id or "na",
            "listing_id": request.listing_id or "na"
        }
        
        # Create Stripe session
        success_url = f"{settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{settings.FRONTEND_URL}/payment/cancelled"
        
        session_id = await stripe_service.create_checkout_session(
            amount=request.amount,
            currency=request.currency.lower(),
            customer_email=user["email"],
            metadata=metadata,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        # Store payment record in database
        payment_doc = {
            "user_id": current_user.user_id,
            "amount": request.amount,
            "currency": request.currency,
            "status": PaymentStatus.PENDING.value,
            "payment_method": PaymentMethod.STRIPE.value,
            "payment_type": request.payment_type,
            "stripe_payment_id": session_id,
            "description": request.description,
            "metadata": metadata,
            "booking_id": request.booking_id,
            "listing_id": request.listing_id,
            "created_at": datetime.utcnow()
        }
        
        result = await db.payments.insert_one(payment_doc)
        
        return {
            "status": "success",
            "session_id": session_id,
            "payment_id": str(result.inserted_id),
            "message": "Checkout session created"
        }
    
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.post("/razorpay/create-order")
async def create_razorpay_order(
    request: CreatePaymentRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a Razorpay order.
    
    Returns order ID to initiate payment.
    """
    try:
        user = await db.users.find_one({"_id": current_user.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        metadata = {
            "user_id": str(current_user.user_id),
            "payment_type": request.payment_type,
            "booking_id": request.booking_id or "na"
        }
        
        # Create Razorpay order
        receipt = f"order_{current_user.user_id}_{datetime.utcnow().timestamp()}"
        order = await razorpay_service.create_order(
            amount=request.amount,
            currency=request.currency.upper(),
            receipt=receipt,
            metadata=metadata
        )
        
        # Store payment record
        payment_doc = {
            "user_id": current_user.user_id,
            "amount": request.amount,
            "currency": request.currency,
            "status": PaymentStatus.PENDING.value,
            "payment_method": PaymentMethod.RAZORPAY.value,
            "payment_type": request.payment_type,
            "razorpay_order_id": order["id"],
            "description": request.description,
            "metadata": metadata,
            "booking_id": request.booking_id,
            "created_at": datetime.utcnow()
        }
        
        result = await db.payments.insert_one(payment_doc)
        
        return {
            "status": "success",
            "order_id": order["id"],
            "payment_id": str(result.inserted_id),
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": settings.RAZORPAY_KEY_ID
        }
    
    except Exception as e:
        logger.error(f"Error creating Razorpay order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create order: {str(e)}"
        )


@router.post("/verify-payment")
async def verify_payment(
    payment_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Verify and complete payment."""
    try:
        payment = await db.payments.find_one({"_id": payment_id})
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        if payment["user_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized"
            )
        
        # Update payment status
        await db.payments.update_one(
            {"_id": payment_id},
            {
                "$set": {
                    "status": PaymentStatus.COMPLETED.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Handle based on payment type
        if payment["payment_type"] == "booking":
            await handle_booking_payment(db, payment, current_user)
        elif payment["payment_type"] == "featured":
            await handle_featured_upgrade(db, payment)
        
        # Send confirmation email
        user = await db.users.find_one({"_id": current_user.user_id})
        await email_service.send_payment_confirmation(
            to_email=user["email"],
            customer_name=user["first_name"],
            amount=payment["amount"],
            currency=payment["currency"],
            transaction_id=str(payment_id),
            description=payment["description"]
        )
        
        logger.info(f"✅ Payment verified: {payment_id}")
        
        return {
            "status": "success",
            "message": "Payment verified and processed",
            "payment_id": str(payment_id)
        }
    
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/payment-status/{payment_id}")
async def get_payment_status(
    payment_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get payment status."""
    try:
        payment = await db.payments.find_one({"_id": payment_id})
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        if payment["user_id"] != current_user.user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        return {
            "payment_id": str(payment["_id"]),
            "status": payment["status"],
            "amount": payment["amount"],
            "currency": payment["currency"],
            "created_at": payment["created_at"].isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting payment status: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refund/{payment_id}")
async def refund_payment(
    payment_id: str,
    reason: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Request refund for payment."""
    try:
        payment = await db.payments.find_one({"_id": payment_id})
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        if payment["user_id"] != current_user.user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Create refund record
        refund_doc = {
            "payment_id": payment_id,
            "user_id": current_user.user_id,
            "amount": payment["amount"],
            "reason": reason,
            "payment_method": payment["payment_method"],
            "status": PaymentStatus.PROCESSING.value,
            "created_at": datetime.utcnow()
        }
        
        refund_result = await db.refunds.insert_one(refund_doc)
        
        # Update payment record
        await db.payments.update_one(
            {"_id": payment_id},
            {
                "$set": {
                    "status": PaymentStatus.REFUNDED.value,
                    "refund_amount": payment["amount"],
                    "refunded_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Refund requested for payment: {payment_id}")
        
        return {
            "status": "success",
            "refund_id": str(refund_result.inserted_id),
            "message": "Refund request processed"
        }
    
    except Exception as e:
        logger.error(f"Error refunding payment: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


async def handle_booking_payment(db, payment: Dict[str, Any], current_user: TokenData):
    """Handle booking payment completion."""
    if payment["booking_id"]:
        await db.bookings.update_one(
            {"_id": payment["booking_id"]},
            {
                "$set": {
                    "payment_status": PaymentStatus.COMPLETED.value,
                    "status": "confirmed",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Notify agent
        booking = await db.bookings.find_one({"_id": payment["booking_id"]})
        if booking:
            notification = {
                "user_id": booking["agent_id"],
                "notification_type": "new_booking",
                "title": "New Booking",
                "message": f"New booking received for property {booking['property_id']}",
                "data": {"booking_id": str(booking["_id"])},
                "created_at": datetime.utcnow()
            }
            await db.notifications.insert_one(notification)


async def handle_featured_upgrade(db, payment: Dict[str, Any]):
    """Handle featured property upgrade."""
    if payment["listing_id"]:
        from datetime import timedelta
        featured_until = datetime.utcnow() + timedelta(days=30)
        
        await db.properties.update_one(
            {"_id": payment["listing_id"]},
            {
                "$set": {
                    "is_featured": True,
                    "featured_until": featured_until,
                    "updated_at": datetime.utcnow()
                }
            }
        )


# ==================== WEBHOOK HANDLERS ====================

@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, str]:
    """Handle Stripe webhook events."""
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        event = StripeService.verify_webhook(payload, sig_header)
        if not event:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        event_type = event["type"]
        event_data = event["data"]["object"]
        
        if event_type == "payment_intent.succeeded":
            await handle_stripe_success(db, event_data)
        elif event_type == "payment_intent.payment_failed":
            await handle_stripe_failure(db, event_data)
        elif event_type == "customer.subscription.updated":
            await handle_subscription_update(db, event_data)
        
        logger.info(f"✅ Stripe webhook processed: {event_type}")
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        return {"status": "failed"}


@router.post("/webhook/razorpay")
async def razorpay_webhook(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, str]:
    """Handle Razorpay webhook events."""
    try:
        payload = await request.json()
        webhook_signature = request.headers.get("X-Razorpay-Signature")
        
        # Verify webhook
        import hmac
        import hashlib
        
        body = await request.body()
        expected_signature = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if webhook_signature != expected_signature:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        event_type = payload.get("event")
        event_data = payload.get("payload", {})
        
        if event_type == "payment.authorized":
            await handle_razorpay_success(db, event_data)
        elif event_type == "payment.failed":
            await handle_razorpay_failure(db, event_data)
        
        logger.info(f"✅ Razorpay webhook processed: {event_type}")
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Razorpay webhook error: {str(e)}")
        return {"status": "failed"}


async def handle_stripe_success(db, payment_data: Dict[str, Any]):
    """Handle Stripe successful payment."""
    payment = await db.payments.find_one(
        {"stripe_payment_id": payment_data["id"]}
    )
    if payment:
        await db.payments.update_one(
            {"_id": payment["_id"]},
            {
                "$set": {
                    "status": PaymentStatus.COMPLETED.value,
                    "stripe_charge_id": payment_data.get("charges", {}).get("data", [{}])[0].get("id"),
                    "updated_at": datetime.utcnow()
                }
            }
        )


async def handle_stripe_failure(db, payment_data: Dict[str, Any]):
    """Handle Stripe failed payment."""
    payment = await db.payments.find_one(
        {"stripe_payment_id": payment_data["id"]}
    )
    if payment:
        await db.payments.update_one(
            {"_id": payment["_id"]},
            {
                "$set": {
                    "status": PaymentStatus.FAILED.value,
                    "error_message": payment_data.get("last_payment_error", {}).get("message"),
                    "updated_at": datetime.utcnow()
                }
            }
        )


async def handle_razorpay_success(db, event_data: Dict[str, Any]):
    """Handle Razorpay successful payment."""
    payment_data = event_data.get("payment", {})
    payment = await db.payments.find_one(
        {"razorpay_payment_id": payment_data["id"]}
    )
    if payment:
        await db.payments.update_one(
            {"_id": payment["_id"]},
            {
                "$set": {
                    "status": PaymentStatus.COMPLETED.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )


async def handle_razorpay_failure(db, event_data: Dict[str, Any]):
    """Handle Razorpay failed payment."""
    payment_data = event_data.get("payment", {})
    payment = await db.payments.find_one(
        {"razorpay_payment_id": payment_data["id"]}
    )
    if payment:
        await db.payments.update_one(
            {"_id": payment["_id"]},
            {
                "$set": {
                    "status": PaymentStatus.FAILED.value,
                    "error_message": payment_data.get("error_description"),
                    "updated_at": datetime.utcnow()
                }
            }
        )


async def handle_subscription_update(db, subscription_data: Dict[str, Any]):
    """Handle subscription status updates."""
    subscription = await db.subscriptions.find_one(
        {"stripe_subscription_id": subscription_data["id"]}
    )
    if subscription:
        status_map = {
            "active": "active",
            "past_due": "active",
            "canceled": "cancelled",
            "unpaid": "suspended"
        }
        new_status = status_map.get(subscription_data["status"], "active")
        
        await db.subscriptions.update_one(
            {"_id": subscription["_id"]},
            {
                "$set": {
                    "status": new_status,
                    "current_period_start": subscription_data["current_period_start"],
                    "current_period_end": subscription_data["current_period_end"],
                    "updated_at": datetime.utcnow()
                }
            }
        )
