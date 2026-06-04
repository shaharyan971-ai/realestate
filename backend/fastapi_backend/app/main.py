"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.database import connect_db, close_db, create_indexes
from app.core.security import verify_token
from app.routers import auth, users, properties, bookings, payments, subscriptions, agents, admin_dashboard

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Starting RealEstate API Server...")
    try:
        await connect_db()
        await create_indexes()
        logger.info("✅ Database connected and indexes created")
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔌 Shutting down server...")
    await close_db()
    logger.info("✅ Server shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="RealEstate API",
    description="Production-ready Real Estate Marketplace API",
    version="1.0.0",
    lifespan=lifespan
)

# Apply rate limiter
app.state.limiter = limiter

# Middleware: Trusted Host (allow all in development)
if settings.ENV == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_ORIGINS
    )
else:
    # In development, allow all hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]
    )

# Middleware: CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=settings.CORS_METHODS.split(",") if isinstance(settings.CORS_METHODS, str) else settings.CORS_METHODS,
    allow_headers=["*"],
    allow_credentials=settings.CORS_CREDENTIALS,
    max_age=3600
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": 422,
            "message": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request, exc):
    """Handle rate limit exceeded."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "status": 429,
            "message": "Too many requests. Please try again later."
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


# API v1 routes placeholder
@app.get("/api/v1/", tags=["API"])
async def api_root():
    """API root endpoint."""
    return {
        "message": "RealEstate API v1",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "properties": "/api/v1/properties",
            "bookings": "/api/v1/bookings",
            "payments": "/api/v1/payments",
            "subscriptions": "/api/v1/subscriptions",
            "agents": "/api/v1/agents",
            "admin": "/api/v1/admin"
        }
    }


# Dependency for getting current user
async def get_current_user(token: str = None):
    """Get current authenticated user from token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return token_data


# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(properties.router)
app.include_router(bookings.router)
app.include_router(payments.router)
app.include_router(subscriptions.router)
app.include_router(agents.router)
app.include_router(admin_dashboard.router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
