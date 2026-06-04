# RealEstate API - Production-Ready FastAPI Backend

A comprehensive, enterprise-grade real estate marketplace API with payment integration, subscription management, booking system, and admin analytics.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Payment Integration](#payment-integration)
- [Webhook Setup](#webhook-setup)
- [Deployment](#deployment)
- [Testing](#testing)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

## ✨ Features

### 💳 Payment System
- **Stripe Integration**: International payments, checkout sessions, subscriptions
- **Razorpay Integration**: India-specific payments (UPI, Cards, Netbanking)
- **Multiple Payment Types**:
  - Property booking fees
  - Premium listing fees
  - Featured upgrades
  - Agent subscriptions
  - Commission-based transactions

### 🏘️ Core Features
- **Property Management**: Advanced listings with images, videos, documents
- **Booking System**: Secure property booking with payment verification
- **Subscription Plans**: Basic, Pro, Enterprise tiers with feature differentiation
- **Agent System**: Agent profiles, KYC verification, ratings, commission tracking
- **Admin Dashboard**: Revenue analytics, booking metrics, subscription tracking

### 🔐 Security & Compliance
- JWT Authentication with refresh tokens
- Role-based access control (User, Agent, Admin)
- Input validation using Pydantic
- Rate limiting
- HTTPS-ready configuration
- Secure environment variable management

### 📧 Notifications
- Email confirmations for bookings
- Payment success notifications
- Subscription expiry reminders
- Admin alerts for critical events

## 🛠️ Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- Motor - Async MongoDB driver
- Pydantic - Data validation
- PyJWT - Authentication
- Stripe SDK - Payment processing
- Razorpay SDK - India payments
- SendGrid - Email service
- APScheduler - Task scheduling

**Database:**
- MongoDB Atlas - Cloud database
- Motor - Async driver

**Deployment:**
- Render or Railway (Backend)
- Vercel (Frontend)
- Cloudinary (Image storage)

## 🏗️ Architecture

```
fastapi_backend/
├── app/
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Configuration management
│   ├── core/
│   │   ├── security.py      # JWT & password hashing
│   │   └── database.py      # MongoDB connection & indexes
│   ├── models/
│   │   └── __init__.py      # Pydantic data models
│   ├── schemas/
│   │   └── __init__.py      # Request/response schemas
│   ├── routers/
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── users.py         # User management
│   │   ├── properties.py    # Property CRUD
│   │   ├── bookings.py      # Booking management
│   │   ├── payments.py      # Payment endpoints & webhooks
│   │   ├── subscriptions.py # Subscription management
│   │   ├── agents.py        # Agent profiles
│   │   └── admin.py         # Admin analytics
│   ├── services/
│   │   ├── payment_service.py    # Stripe & Razorpay
│   │   ├── email_service.py      # Email notifications
│   │   ├── booking_service.py    # Booking logic
│   │   ├── subscription_service.py
│   │   └── analytics_service.py
│   └── utils/
│       ├── validators.py    # Input validation helpers
│       ├── decorators.py    # Custom decorators
│       └── helpers.py       # Utility functions
├── requirements.txt
├── .env.example
├── README.md
└── Dockerfile (for containerization)
```

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- MongoDB Atlas account
- Stripe account (for international payments)
- Razorpay account (for India payments)
- SendGrid account (for emails)
- Cloudinary account (for image storage)

### Local Development

1. **Clone repository**
```bash
git clone <repository-url>
cd fastapi_backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Run development server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

## ⚙️ Configuration

### Environment Variables (.env)

```
# Database
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/realestate_db
MONGODB_DB_NAME=realestate_db

# Server
ENV=development
DEBUG=True
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# JWT
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
JWT_REFRESH_EXPIRATION_DAYS=30

# Stripe
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Razorpay
RAZORPAY_KEY_ID=xxx
RAZORPAY_KEY_SECRET=xxx

# Email
SENDGRID_API_KEY=xxx
SENDGRID_FROM_EMAIL=noreply@realestate.app

# Payment Amounts (in paise/cents)
BOOKING_FEE_AMOUNT=500
LISTING_FEE_AMOUNT=999
FEATURED_UPGRADE_FEE=2999
ADMIN_COMMISSION_PERCENT=10
```

## 📚 API Endpoints

### Authentication
```
POST   /api/v1/auth/register          - Register user
POST   /api/v1/auth/login              - Login user
POST   /api/v1/auth/refresh            - Refresh token
POST   /api/v1/auth/logout             - Logout user
```

### Properties
```
GET    /api/v1/properties              - List all properties
POST   /api/v1/properties              - Create property
GET    /api/v1/properties/{id}         - Get property details
PUT    /api/v1/properties/{id}         - Update property
DELETE /api/v1/properties/{id}         - Delete property
GET    /api/v1/properties/search       - Search with filters
POST   /api/v1/properties/{id}/images  - Upload images
```

### Bookings
```
GET    /api/v1/bookings                - List user bookings
POST   /api/v1/bookings                - Create booking
GET    /api/v1/bookings/{id}           - Get booking details
PUT    /api/v1/bookings/{id}           - Update booking
DELETE /api/v1/bookings/{id}           - Cancel booking
```

### Payments
```
POST   /api/v1/payments/stripe/checkout    - Create Stripe checkout
POST   /api/v1/payments/razorpay/order     - Create Razorpay order
POST   /api/v1/payments/verify             - Verify payment
GET    /api/v1/payments/history            - Payment history
POST   /api/v1/payments/refund/{id}        - Request refund
```

### Subscriptions
```
GET    /api/v1/subscriptions/plans         - List all plans
POST   /api/v1/subscriptions               - Create subscription
GET    /api/v1/subscriptions/current       - Get current subscription
PUT    /api/v1/subscriptions/{id}/cancel   - Cancel subscription
POST   /api/v1/subscriptions/{id}/renew    - Renew subscription
```

### Agents
```
GET    /api/v1/agents/{id}                 - Get agent profile
POST   /api/v1/agents/register             - Register as agent
PUT    /api/v1/agents/kyc                  - Upload KYC documents
GET    /api/v1/agents/{id}/properties      - Agent listings
GET    /api/v1/agents/{id}/earnings        - Agent earnings
```

### Admin
```
GET    /api/v1/admin/analytics             - Dashboard analytics
GET    /api/v1/admin/payments/report       - Payment reports
GET    /api/v1/admin/users                 - User management
PUT    /api/v1/admin/users/{id}/role       - Update user role
GET    /api/v1/admin/subscriptions         - Subscription management
```

## 📦 Database Schema

### Collections

**users**
```json
{
  "_id": ObjectId,
  "email": "user@example.com",
  "password_hash": "hashed_value",
  "full_name": "John Doe",
  "phone": "+919999999999",
  "profile_image": "url",
  "role": "user|agent|admin",
  "is_verified": false,
  "is_active": true,
  "address": "123 Main St",
  "city": "Mumbai",
  "state": "Maharashtra",
  "pincode": "400001",
  "preferences": {},
  "created_at": ISODate,
  "updated_at": ISODate,
  "last_login": ISODate
}
```

**properties**
```json
{
  "_id": ObjectId,
  "owner_id": ObjectId,
  "agent_id": ObjectId,
  "title": "Luxury Villa",
  "description": "Beautiful villa...",
  "property_type": "residential|commercial|land",
  "status": "active|sold|rented|inactive",
  "address": "123 Palm Ave",
  "city": "Mumbai",
  "latitude": 19.0760,
  "longitude": 72.8777,
  "bedrooms": 4,
  "bathrooms": 2,
  "total_area": 5000,
  "price": 5000000,
  "amenities": ["WiFi", "Pool", "Parking"],
  "images": ["url1", "url2"],
  "is_featured": true,
  "featured_until": ISODate,
  "views": 150,
  "favorites_count": 25,
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**bookings**
```json
{
  "_id": ObjectId,
  "property_id": ObjectId,
  "buyer_id": ObjectId,
  "agent_id": ObjectId,
  "status": "pending|confirmed|completed|cancelled",
  "visit_date": ISODate,
  "amount": 500,
  "payment_id": ObjectId,
  "payment_status": "pending|completed|failed",
  "notes": "Optional notes",
  "created_at": ISODate,
  "updated_at": ISODate,
  "confirmed_at": ISODate
}
```

**payments**
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "amount": 5000,
  "currency": "INR",
  "payment_method": "stripe|razorpay|card|upi",
  "status": "pending|completed|failed|refunded",
  "stripe_payment_id": "pi_xxx",
  "razorpay_payment_id": "pay_xxx",
  "description": "Property booking",
  "metadata": {
    "booking_id": ObjectId,
    "property_id": ObjectId,
    "property_title": "Luxury Villa"
  },
  "refund_amount": 0,
  "created_at": ISODate,
  "completed_at": ISODate
}
```

**subscriptions**
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "plan": "basic|pro|enterprise",
  "status": "active|expired|cancelled|pending",
  "amount": 499,
  "currency": "INR",
  "billing_cycle": "monthly|yearly",
  "stripe_subscription_id": "sub_xxx",
  "razorpay_subscription_id": "sub_xxx",
  "started_at": ISODate,
  "active_until": ISODate,
  "max_listings": 5,
  "features": ["Feature1", "Feature2"],
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**agents**
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "registration_number": "REG123",
  "license_number": "LIC456",
  "commission_rate": 10.0,
  "kyc_verified": false,
  "kyc_documents": {
    "aadhar": "url",
    "pan": "url",
    "license": "url"
  },
  "total_sales": 12,
  "total_earnings": 45000,
  "rating": 4.5,
  "reviews_count": 8,
  "bank_account": "1234567890",
  "is_active": true,
  "created_at": ISODate
}
```

## 💳 Payment Integration

### Stripe Setup

1. **Create API Keys**
   - Go to Stripe Dashboard → Developers → API Keys
   - Copy Secret Key and Publishable Key
   - Add to `.env`

2. **Create Products and Plans**
```bash
# Basic Plan
stripe plans create --amount 49900 --currency inr --interval month --product-id prod_xxx

# Pro Plan
stripe plans create --amount 199900 --currency inr --interval month --product-id prod_xxx

# Enterprise Plan
stripe plans create --amount 499900 --currency inr --interval month --product-id prod_xxx
```

3. **Webhook Setup**
   - Go to Stripe Dashboard → Developers → Webhooks
   - Add endpoint: `https://yourdomain.com/api/v1/payments/webhook/stripe`
   - Select events: `charge.succeeded`, `charge.failed`, `customer.subscription.updated`
   - Copy Signing Secret to `.env` as `STRIPE_WEBHOOK_SECRET`

### Razorpay Setup

1. **Get API Keys**
   - Go to Razorpay Dashboard → Settings → API Keys
   - Copy Key ID and Key Secret
   - Add to `.env`

2. **Create Plans**
```bash
# Using Razorpay Dashboard or API
{
  "period": "monthly",
  "interval": 1,
  "item": {
    "active": true,
    "description": "Basic Plan",
    "amount": 49900,
    "currency": "INR"
  }
}
```

3. **Webhook Setup**
   - Go to Razorpay Dashboard → Settings → Webhooks
   - Add endpoint: `https://yourdomain.com/api/v1/payments/webhook/razorpay`
   - Select events: `payment.authorized`, `payment.failed`, `subscription.activated`
   - Note the Signing Secret

## 🔗 Webhook Setup

### Webhook Handler Structure

```python
@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    event = stripe_service.verify_webhook(payload, sig_header)
    if not event:
        return {"error": "Invalid signature"}
    
    if event["type"] == "charge.succeeded":
        await handle_payment_success(event["data"]["object"])
    elif event["type"] == "charge.failed":
        await handle_payment_failed(event["data"]["object"])
    
    return {"received": True}
```

## 🚀 Deployment

### Render Deployment

1. **Connect Repository**
   - Go to Render.com → New → Web Service
   - Connect GitHub repository
   - Select Python environment

2. **Configure Environment**
   - Add all `.env` variables in Render dashboard
   - Set Python version: 3.10
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

3. **Deploy**
   - Render automatically deploys on push to main branch

### Manual Deployment with Docker

1. **Create Dockerfile**
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Build and Run**
```bash
docker build -t realestate-api .
docker run -p 8000:8000 --env-file .env realestate-api
```

### MongoDB Atlas Setup

1. Create cluster on MongoDB Atlas
2. Set IP whitelist (or allow all: 0.0.0.0)
3. Create database user
4. Get connection string
5. Replace in `MONGODB_URL`

## 🧪 Testing

### Unit Tests
```bash
pytest tests/unit --cov=app
```

### Integration Tests
```bash
pytest tests/integration
```

### Load Testing
```bash
locust -f tests/locust/locustfile.py --host=http://localhost:8000
```

### Sample Test
```python
import pytest
from app.core.security import hash_password, verify_password

def test_password_hashing():
    password = "TestPassword123"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)
```

## 🔐 Security Best Practices

1. **Environment Variables**: All sensitive data in `.env`
2. **JWT Secrets**: Min 32 characters, change in production
3. **CORS**: Specify exact origins, not `*` in production
4. **Rate Limiting**: Implement across all endpoints
5. **Input Validation**: Use Pydantic for all requests
6. **HTTPS**: Enforce in production
7. **SQL Injection**: Not applicable (MongoDB), but validate input
8. **CSRF**: Include CSRF tokens for state-changing operations
9. **Secrets Scanning**: Use pre-commit hooks
10. **Dependency Updates**: Regular security updates

## 🐛 Troubleshooting

### Connection Issues

**MongoDB Connection Failed**
```
Solution: Check MONGODB_URL format, IP whitelist, credentials
```

**Stripe API Error**
```
Solution: Verify STRIPE_SECRET_KEY, check Stripe API status
```

### Payment Issues

**Webhook Not Triggering**
```
Solution: Check endpoint URL, verify signing secret, check logs
```

**Payment Status Not Updating**
```
Solution: Manually trigger webhook, check database connection, verify payment ID
```

### Performance Issues

**Slow Queries**
```
Solution: Check database indexes, enable query profiling
mongosh
db.setProfilingLevel(1)
db.system.profile.find().sort({ts: -1}).limit(5).pretty()
```

## 📝 Contributing

1. Create feature branch
2. Make changes
3. Add tests
4. Create pull request
5. Deploy to staging for review

## 📄 License

Proprietary - RealEstate Marketplace

## 🤝 Support

For issues and support:
- GitHub Issues
- Email: support@realestate.app
- Discord: [Community Server Link]

---

**Made with ❤️ by RealEstate Team**
Production-ready | Scalable | Secure
