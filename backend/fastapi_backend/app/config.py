"""Configuration management for FastAPI application."""
import os
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Application Settings with environment variable validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "realestate_db"
    
    # Server
    ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    
    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JWT_REFRESH_EXPIRATION_DAYS: int = 30
    
    # Stripe Configuration
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_BASIC_PLAN_ID: str = ""
    STRIPE_PRO_PLAN_ID: str = ""
    STRIPE_ENTERPRISE_PLAN_ID: str = ""
    
    # Razorpay Configuration
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    
    # Email Configuration
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@realestate.app"
    SENDGRID_FROM_NAME: str = "RealEstate"
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    
    # Payment
    BOOKING_FEE_AMOUNT: int = 500  # In paise for India, cents for international
    LISTING_FEE_AMOUNT: int = 999
    FEATURED_UPGRADE_FEE: int = 2999
    ADMIN_COMMISSION_PERCENT: float = 10.0
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    
    # Security
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_HEADERS: str = "*"
    
    # Admin
    ADMIN_EMAIL: str = "admin@realestate.app"
    ADMIN_PHONE: str = "+919999999999"
    
    # Feature Flags
    ENABLE_RAZORPAY: bool = True
    ENABLE_STRIPE: bool = True
    ENABLE_EMAIL_NOTIFICATIONS: bool = True
    ENABLE_IMAGE_UPLOAD: bool = True
    
    # Branding
    LOGO_URL: str = "https://realestate.app/static/logo.png"
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("CORS_METHODS", mode="before")
    @classmethod
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v
    
    @property
    def mongodb_url(self) -> str:
        """Get MongoDB URL ensuring proper format."""
        return self.MONGODB_URL
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENV == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENV == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Initialize settings
settings = get_settings()
