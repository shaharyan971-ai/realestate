"""Request and response schemas for API endpoints."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from enum import Enum
from app.models import *


# Enums
class PaymentMethod(str, Enum):
    """Payment method types."""
    STRIPE = "stripe"
    RAZORPAY = "razorpay"
    CARD = "card"
    UPI = "upi"


class SubscriptionPlanEnum(str, Enum):
    """Subscription plan types."""
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"



# Response Schemas
class PaymentSchema(BaseModel):
    """Payment response schema."""
    id: str
    user_id: str
    amount: float
    currency: str
    status: str
    payment_method: str
    created_at: datetime


class BookingSchema(BaseModel):
    """Booking response schema."""
    id: str
    property_id: str
    buyer_id: str
    visit_date: datetime
    status: str
    payment_status: str
    amount: float
    created_at: datetime


class SubscriptionSchema(BaseModel):
    """Subscription response schema."""
    id: str
    user_id: str
    plan: str
    status: str
    amount: float
    active_until: datetime
    created_at: datetime


# Booking Schemas
class CreateBookingRequest(BaseModel):
    """Request schema for creating a booking."""
    property_id: str
    visit_date: datetime
    notes: Optional[str] = None


class UpdateBookingRequest(BaseModel):
    """Request schema for updating a booking."""
    visit_date: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[str] = None


# Property Schemas
class CreatePropertyRequest(BaseModel):
    """Request schema for creating a property."""
    title: str
    description: str
    property_type: str
    address: str
    city: str
    state: str
    pincode: str
    latitude: float
    longitude: float
    bedrooms: int
    bathrooms: int
    total_area: float
    price: float
    amenities: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    furnished: Optional[str] = None


class UpdatePropertyRequest(BaseModel):
    """Request schema for updating a property."""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = None
    amenities: Optional[List[str]] = None
    images: Optional[List[str]] = None


# User Schemas
class CreateUserRequest(BaseModel):
    """Request schema for user registration."""
    email: EmailStr
    password: str
    full_name: str
    phone: str
    role: Optional[str] = "user"


class LoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr
    password: str


class UpdateUserRequest(BaseModel):
    """Request schema for updating user profile."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None


# Payment Schemas
class CreatePaymentRequest(BaseModel):
    """Request schema for creating a payment."""
    booking_id: str
    payment_method: str
    amount: float


class PaymentWebhookRequest(BaseModel):
    """Request schema for payment webhooks."""
    event_type: str
    payment_id: str
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Subscription Schemas
class CreateSubscriptionRequest(BaseModel):
    """Request schema for creating a subscription."""
    plan: str
    billing_cycle: str = "monthly"


class UpdateSubscriptionRequest(BaseModel):
    """Request schema for updating a subscription."""
    plan: Optional[str] = None
    billing_cycle: Optional[str] = None


# Agent Schemas
class CreateAgentRequest(BaseModel):
    """Request schema for agent registration."""
    registration_number: str
    license_number: str
    commission_rate: float = 10.0


class UpdateAgentRequest(BaseModel):
    """Request schema for updating agent profile."""
    registration_number: Optional[str] = None
    license_number: Optional[str] = None
    commission_rate: Optional[float] = None
    bank_account: Optional[str] = None
    bank_code: Optional[str] = None
    bank_name: Optional[str] = None
