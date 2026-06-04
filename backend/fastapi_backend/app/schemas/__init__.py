"""Pydantic request/response schemas for API operations."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models import PropertyType, PaymentStatus, SubscriptionPlan


# ========================= USER SCHEMAS =========================

class UserRegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    phone: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v


class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response."""
    id: Optional[str] = Field(None, alias="_id")
    email: str
    full_name: str
    phone: str
    role: str
    is_verified: bool
    profile_image: Optional[str] = None
    
    class Config:
        populate_by_name = True


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# ========================= PROPERTY SCHEMAS =========================

class PropertyCreateRequest(BaseModel):
    """Create property request."""
    title: str
    description: str
    property_type: PropertyType
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
    furnished: Optional[str] = None
    under_construction: bool = False


class PropertyUpdateRequest(BaseModel):
    """Update property request."""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    total_area: Optional[float] = None
    amenities: Optional[List[str]] = None


class PropertyResponse(BaseModel):
    """Property response."""
    id: str = Field(alias="_id")
    title: str
    description: str
    property_type: str
    price: float
    location: str
    bedrooms: int
    bathrooms: int
    images: List[str]
    is_featured: bool
    views: int
    created_at: datetime
    
    class Config:
        populate_by_name = True


# ========================= PAYMENT SCHEMAS =========================

class PaymentInitializeRequest(BaseModel):
    """Initialize payment request."""
    amount: float
    currency: str = "INR"
    payment_method: str  # "stripe", "razorpay", "card", "upi"
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StripeCheckoutRequest(BaseModel):
    """Stripe checkout request."""
    amount: float
    currency: str = "INR"
    metadata: Dict[str, Any]
    success_url: str
    cancel_url: str


class RazorpayOrderRequest(BaseModel):
    """Razorpay order request."""
    amount: float
    currency: str = "INR"
    receipt: str
    metadata: Dict[str, Any]


class PaymentWebhookRequest(BaseModel):
    """Payment webhook request."""
    event: str
    data: Dict[str, Any]


class PaymentResponse(BaseModel):
    """Payment response."""
    id: str = Field(alias="_id")
    amount: float
    status: str
    payment_method: str
    created_at: datetime
    
    class Config:
        populate_by_name = True


# ========================= SUBSCRIPTION SCHEMAS =========================

class SubscriptionCreateRequest(BaseModel):
    """Create subscription request."""
    plan: SubscriptionPlan
    billing_cycle: str = "monthly"


class SubscriptionResponse(BaseModel):
    """Subscription response."""
    id: str = Field(alias="_id")
    plan: str
    status: str
    active_until: datetime
    max_listings: int
    created_at: datetime
    
    class Config:
        populate_by_name = True


# ========================= BOOKING SCHEMAS =========================

class BookingCreateRequest(BaseModel):
    """Create booking request."""
    property_id: str
    visit_date: datetime
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    """Booking response."""
    id: str = Field(alias="_id")
    property_id: str
    status: str
    visit_date: datetime
    payment_status: str
    created_at: datetime
    
    class Config:
        populate_by_name = True


# ========================= AGENT SCHEMAS =========================

class AgentRegistrationRequest(BaseModel):
    """Agent registration request."""
    registration_number: str
    license_number: str
    commission_rate: float = 10.0
    bank_account: str
    bank_code: str
    bank_name: str


class AgentResponse(BaseModel):
    """Agent response."""
    id: str = Field(alias="_id")
    full_name: str
    email: str
    phone: str
    kyc_verified: bool
    rating: float
    total_sales: int
    
    class Config:
        populate_by_name = True


# ========================= REVIEW SCHEMAS =========================

class ReviewCreateRequest(BaseModel):
    """Create review request."""
    rating: int = Field(ge=1, le=5)
    title: str
    content: str
    agent_id: Optional[str] = None
    property_id: Optional[str] = None


class ReviewResponse(BaseModel):
    """Review response."""
    id: str = Field(alias="_id")
    rating: int
    title: str
    content: str
    reviewer_name: str
    created_at: datetime
    
    class Config:
        populate_by_name = True


# ========================= ANALYTICS SCHEMAS =========================

class AnalyticsResponse(BaseModel):
    """Analytics dashboard response."""
    total_revenue: float
    monthly_revenue: Dict[str, float]
    active_subscriptions: int
    total_bookings: int
    completed_bookings: int
    total_properties: int
    conversion_rate: float
    top_agents: List[Dict[str, Any]]
    top_properties: List[Dict[str, Any]]


# ========================= ERROR SCHEMAS =========================

class ErrorResponse(BaseModel):
    """Error response."""
    status: int
    message: str
    error: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    status: int = 422
    message: str = "Validation error"
    errors: List[Dict[str, Any]]
