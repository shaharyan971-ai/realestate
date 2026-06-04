"""Pytest configuration and fixtures."""
import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """Create test database connection."""
    # Use a separate test database
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client["test_realestate_db"]
    
    yield db
    
    # Cleanup: drop test database
    await client.drop_database("test_realestate_db")
    client.close()


@pytest.fixture(autouse=True)
async def clean_db(test_db):
    """Clean database before each test."""
    # Drop all collections
    for collection_name in await test_db.list_collection_names():
        await test_db[collection_name].drop()
    
    yield
    
    # Cleanup after test
    for collection_name in await test_db.list_collection_names():
        await test_db[collection_name].drop()


@pytest.fixture
async def test_user(test_db):
    """Create a test user."""
    from app.core.security import hash_password
    from datetime import datetime
    
    user = {
        "email": "testuser@example.com",
        "password_hash": hash_password("TestPassword123"),
        "full_name": "Test User",
        "phone": "+1234567890",
        "role": "user",
        "is_verified": False,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await test_db.users.insert_one(user)
    user["_id"] = result.inserted_id
    
    return user


@pytest.fixture
async def test_agent(test_db):
    """Create a test agent user."""
    from app.core.security import hash_password
    from datetime import datetime
    
    user = {
        "email": "testagent@example.com",
        "password_hash": hash_password("TestPassword123"),
        "full_name": "Test Agent",
        "phone": "+1234567890",
        "role": "agent",
        "is_verified": True,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await test_db.users.insert_one(user)
    user["_id"] = result.inserted_id
    
    return user


@pytest.fixture
async def test_property(test_db, test_agent):
    """Create a test property."""
    from datetime import datetime
    
    property_doc = {
        "owner_id": test_agent["_id"],
        "agent_id": test_agent["_id"],
        "title": "Test Property",
        "description": "A beautiful test property",
        "property_type": "residential",
        "status": "active",
        "address": "123 Test St",
        "city": "Test City",
        "state": "Test State",
        "pincode": "12345",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "bedrooms": 3,
        "bathrooms": 2,
        "total_area": 2000.0,
        "price": 500000.0,
        "amenities": ["WiFi", "Parking"],
        "images": [],
        "is_featured": False,
        "views": 0,
        "favorites_count": 0,
        "booking_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await test_db.properties.insert_one(property_doc)
    property_doc["_id"] = result.inserted_id
    
    return property_doc


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test user."""
    from app.core.security import create_token_pair
    
    tokens = create_token_pair(
        user_id=str(test_user["_id"]),
        email=test_user["email"],
        role=test_user["role"]
    )
    
    return {"Authorization": f"Bearer {tokens['access_token']}"}
