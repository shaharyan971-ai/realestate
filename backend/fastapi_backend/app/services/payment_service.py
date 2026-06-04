"""Payment services integration."""
from typing import Dict, Any, Optional
import stripe
import razorpay
import logging
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class StripeService:
    """Stripe payment service."""
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    async def create_checkout_session(
        self,
        amount: float,
        currency: str,
        customer_email: str,
        metadata: Dict[str, Any],
        success_url: str,
        cancel_url: str
    ) -> str:
        """Create Stripe checkout session."""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": currency.lower(),
                        "unit_amount": int(amount * 100),  # Convert to cents
                        "product_data": {
                            "name": metadata.get("description", "RealEstate Purchase"),
                        },
                    },
                    "quantity": 1,
                }],
                mode="payment",
                customer_email=customer_email,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata
            )
            logger.info(f"✅ Stripe session created: {session.id}")
            return session.id
        except stripe.error.StripeError as e:
            logger.error(f"❌ Stripe error: {str(e)}")
            raise
    
    async def create_subscription(
        self,
        customer_email: str,
        plan_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Stripe subscription."""
        try:
            # Find or create customer
            customers = stripe.Customer.list(email=customer_email, limit=1)
            if customers.data:
                customer_id = customers.data[0].id
            else:
                customer = stripe.Customer.create(email=customer_email)
                customer_id = customer.id
            
            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": plan_id}],
                metadata=metadata
            )
            
            logger.info(f"✅ Subscription created: {subscription.id}")
            return {
                "subscription_id": subscription.id,
                "customer_id": customer_id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end
            }
        except stripe.error.StripeError as e:
            logger.error(f"❌ Stripe subscription error: {str(e)}")
            raise
    
    @staticmethod
    def verify_webhook(payload: bytes, sig_header: str) -> Optional[Dict[str, Any]]:
        """Verify Stripe webhook signature."""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"❌ Webhook signature verification failed: {str(e)}")
            return None


class RazorpayService:
    """Razorpay payment service."""
    
    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    
    async def create_order(
        self,
        amount: float,
        currency: str,
        receipt: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Razorpay order."""
        try:
            order = self.client.order.create(
                amount=int(amount * 100),  # Convert to paise
                currency=currency.upper(),
                receipt=receipt,
                notes=metadata
            )
            logger.info(f"✅ Razorpay order created: {order['id']}")
            return order
        except Exception as e:
            logger.error(f"❌ Razorpay error: {str(e)}")
            raise
    
    async def create_subscription(
        self,
        plan_id: str,
        customer_notify: int = 1,
        quantity: int = 1,
        total_count: int = 12,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create Razorpay subscription."""
        try:
            subscription = self.client.subscription.create(
                plan_id=plan_id,
                customer_notify=customer_notify,
                quantity=quantity,
                total_count=total_count,
                notes=metadata or {}
            )
            logger.info(f"✅ Razorpay subscription created: {subscription['id']}")
            return subscription
        except Exception as e:
            logger.error(f"❌ Razorpay subscription error: {str(e)}")
            raise
    
    @staticmethod
    def verify_payment_signature(
        order_id: str,
        payment_id: str,
        signature: str
    ) -> bool:
        """Verify Razorpay payment signature."""
        try:
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            return client.utility.verify_payment_signature({
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            })
        except Exception as e:
            logger.error(f"❌ Razorpay signature verification failed: {str(e)}")
            return False


# Plan configurations
SUBSCRIPTION_PLANS = {
    "basic": {
        "name": "Basic",
        "max_listings": 5,
        "amount": 499,
        "currency": "INR",
        "features": ["5 listings", "Standard support"],
        "stripe_plan_id": settings.STRIPE_BASIC_PLAN_ID,
    },
    "pro": {
        "name": "Pro",
        "max_listings": 25,
        "amount": 1999,
        "currency": "INR",
        "features": ["25 listings", "Featured badge", "Priority ranking", "Analytics"],
        "stripe_plan_id": settings.STRIPE_PRO_PLAN_ID,
    },
    "enterprise": {
        "name": "Enterprise",
        "max_listings": 999,
        "amount": 4999,
        "currency": "INR",
        "features": ["Unlimited listings", "Homepage spotlight", "Advanced analytics", "Dedicated support"],
        "stripe_plan_id": settings.STRIPE_ENTERPRISE_PLAN_ID,
    }
}


# Initialize services
stripe_service = StripeService()
razorpay_service = RazorpayService()
