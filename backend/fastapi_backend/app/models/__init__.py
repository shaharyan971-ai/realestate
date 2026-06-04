"""MongoDB models/schemas for database documents."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from bson import ObjectId


class ObjectIdStr(str):
    """Custom ObjectId handling for Pydantic."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError(f'Invalid ObjectId: {v}')
        return ObjectId(v)


class UserRole(str, Enum):
    """User role types."""
    USER = "user"
    AGENT = "agent"
    ADMIN = "admin"


class PropertyType(str, Enum):
    """Property types."""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    LAND = "land"


class PropertyStatus(str, Enum):
    """Property listing status."""
    ACTIVE = "active"
    SOLD = "sold"
    RENTED = "rented"
    INACTIVE = "inactive"


class PaymentStatus(str, Enum):
    """Payment status."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class SubscriptionPlan(str, Enum):
    """Subscription plan types."""
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


class BookingStatus(str, Enum):
    """Booking status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UserModel(BaseModel):
    """User database model."""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        from_attributes=True,
        json_encoders={ObjectId: str}
    )
    id: Optional[ObjectId] = Field(None, alias="_id")
    email: EmailStr
    password_hash: str
    full_name: str
    phone: str
    profile_image: Optional[str] = None
    role: UserRole = UserRole.USER
    is_verified: bool = False
    is_active: bool = True
    
    # Address
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    
    # Preferences
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None


class AgentModel(BaseModel):
    """Agent profile model."""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        json_encoders={ObjectId: str}
    )
    id: Optional[ObjectId] = Field(None, alias="_id")
    user_id: ObjectId
    registration_number: str
    license_number: str
    commission_rate: float = 10.0  # Percentage
    
    # KYC Status
    kyc_verified: bool = False
    kyc_documents: Dict[str, str] = Field(default_factory=dict)  # file_type: url
    kyc_submitted_at: Optional[datetime] = None
    kyc_verified_at: Optional[datetime] = None
    
    # Performance
    total_sales: int = 0
    total_earnings: float = 0.0
    rating: float = 0.0
    reviews_count: int = 0
    
    # Bank Details
    bank_account: Optional[str] = None
    bank_code: Optional[str] = None
    bank_name: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PropertyModel(BaseModel):
    """Property listing model."""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        json_encoders={ObjectId: str}
    )
    id: Optional[ObjectId] = Field(None, alias="_id")
    owner_id: ObjectId  # User or Agent ID
    agent_id: Optional[ObjectId] = None
    
    # Basic Info
    title: str
    description: str
    property_type: PropertyType
    status: PropertyStatus = PropertyStatus.ACTIVE
    
    # Location
    address: str
    city: str
    state: str
    pincode: str
    latitude: float
    longitude: float
    
    # Details
    bedrooms: int
    bathrooms: int
    total_area: float  # in sqft
    plot_area: Optional[float] = None
    
    # Prices
    price: float
    expected_price: Optional[float] = None
    price_per_sqft: Optional[float] = None
    
    # Amenities
    amenities: List[str] = Field(default_factory=list)
    
    # Media
    images: List[str] = Field(default_factory=list)  # URLs from Cloudinary
    floor_plan: Optional[str] = None  # PDF URL
    virtual_tour_url: Optional[str] = None  # Video URL
    documents: List[Dict[str, str]] = Field(default_factory=list)  # {type: url}
    
    # Features
    is_featured: bool = False
    is_boosted: bool = False
    featured_until: Optional[datetime] = None
    boost_until: Optional[datetime] = None
    
    # Availability
    available_from: Optional[datetime] = None
    furnished: Optional[str] = None  # "furnished", "semi-furnished", "unfurnished"
    under_construction: bool = False
    
    # Engagement
    views: int = 0
    favorites_count: int = 0
    booking_count: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BookingModel(BaseModel):
    """Property booking model."""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        json_encoders={ObjectId: str}
    )
    id: Optional[ObjectId] = Field(None, alias="_id")
    property_id: ObjectId
    buyer_id: ObjectId
    agent_id: ObjectId
    
    # Booking Details
    status: BookingStatus = BookingStatus.PENDING
    visit_date: datetime
    notes: Optional[str] = None
    
    # Payment
    amount: float
    payment_id: Optional[ObjectId] = None
    payment_status: PaymentStatus = PaymentStatus.PENDING
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class PaymentModel(BaseModel):
    """Payment transaction model."""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        json_encoders={ObjectId: str}
    )
    id: Optional[ObjectId] = Field(None, alias="_id")
    user_id: ObjectId
    amount: float
    currency: str = "INR"  # or USD
    
    # Payment Info
    payment_method: str  # "stripe", "razorpay", "card", "upi"
    status: PaymentStatus = PaymentStatus.PENDING
    
    # External References
    stripe_payment_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    
    # Transaction Details
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)  # booking_id, property_id, etc.
    
    # Refund
    refund_id: Optional[str] = None
    refund_amount: Optional[float] = None
    refund_reason: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class SubscriptionModel(BaseModel):
    """Subscription model."""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        json_encoders={ObjectId: str}
    )
    id: Optional[ObjectId] = Field(None, alias="_id")
    user_id: ObjectId
    plan: SubscriptionPlan
    status: SubscriptionStatus = SubscriptionStatus.PENDING
    
    # Pricing
    amount: float
    currency: str = "INR"
    billing_cycle: str = "monthly"  # "monthly", "yearly"
    
    # Payment
    stripe_subscription_id: Optional[str] = None
    razorpay_subscription_id: Optional[str] = None
    
    # Dates
    started_at: Optional[datetime] = None
    active_until: datetime
    renews_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Features
    max_listings: int
    features: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FavoriteModel(BaseModel):
    """Favorite property model."""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        json_encoders={ObjectId: str}
    )
    id: Optional[ObjectId] = Field(None, alias="_id")
    user_id: ObjectId
    property_id: ObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewModel(BaseModel):
    """Review/Rating model."""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        json_encoders={ObjectId: str}
    )
    id: Optional[ObjectId] = Field(None, alias="_id")
    reviewer_id: ObjectId
    agent_id: Optional[ObjectId] = None
    property_id: Optional[ObjectId] = None
    
    rating: int = Field(ge=1, le=5)
    title: str
    content: str
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationModel(BaseModel):
    """Notification model."""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        json_encoders={ObjectId: str}
    )
    id: Optional[ObjectId] = Field(None, alias="_id")
    user_id: ObjectId
    title: str
    content: str
    type: str  # "booking", "payment", "subscription", "agent", "admin"
    is_read: bool = False
    
    related_id: Optional[ObjectId] = None  # ID of related entity
    action_url: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnalyticsModel(BaseModel):
    """Analytics/Metrics model."""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        json_encoders={ObjectId: str}
    )
    id: Optional[ObjectId] = Field(None, alias="_id")
    
    # Revenue
    total_revenue: float = 0.0
    monthly_revenue: Dict[str, float] = Field(default_factory=dict)
    
    # Bookings
    total_bookings: int = 0
    completed_bookings: int = 0
    pending_bookings: int = 0
    
    # Subscriptions
    active_subscriptions: int = 0
    total_subscriptions: int = 0
    
    # Properties
    total_properties: int = 0
    active_properties: int = 0
    featured_properties: int = 0
    
    # Users
    total_users: int = 0
    total_agents: int = 0
    
    # Conversion
    conversion_rate: float = 0.0
    
    # Top Performers
    top_agents: List[Dict[str, Any]] = Field(default_factory=list)
    top_properties: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Timestamps
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
