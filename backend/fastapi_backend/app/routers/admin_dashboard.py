"""Admin dashboard analytics routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import verify_token, TokenData
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/admin/dashboard", tags=["admin-dashboard"])

async def get_admin_user(token: str = None) -> TokenData:
    user = verify_token(token)
    if not user or user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user

@router.get("/overview")
async def dashboard_overview(db: AsyncIOMotorDatabase = Depends(get_db), current_user: TokenData = Depends(get_admin_user)) -> Dict[str, Any]:
    """Get admin dashboard overview metrics."""
    try:
        now = datetime.utcnow()
        month_ago = now - timedelta(days=30)
        # Revenue
        total_revenue = await db.payments.aggregate([
            {"$match": {"status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        total_revenue = total_revenue[0]["total"] if total_revenue else 0.0
        # Monthly revenue
        monthly_revenue = await db.payments.aggregate([
            {"$match": {"status": "completed", "created_at": {"$gte": month_ago}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        monthly_revenue = monthly_revenue[0]["total"] if monthly_revenue else 0.0
        # Active subscriptions
        active_subs = await db.subscriptions.count_documents({"status": "active"})
        # Bookings
        total_bookings = await db.bookings.count_documents({})
        completed_bookings = await db.bookings.count_documents({"status": "completed"})
        # Top agents
        top_agents = await db.agents.find().sort("total_earnings", -1).limit(5).to_list(5)
        # Property engagement
        top_properties = await db.properties.find().sort("views", -1).limit(5).to_list(5)
        return {
            "total_revenue": total_revenue,
            "monthly_revenue": monthly_revenue,
            "active_subscriptions": active_subs,
            "total_bookings": total_bookings,
            "completed_bookings": completed_bookings,
            "top_agents": [{"id": str(a["_id"]), "name": a.get("agency_name"), "total_earnings": a.get("total_earnings", 0)} for a in top_agents],
            "top_properties": [{"id": str(p["_id"]), "title": p.get("title"), "views": p.get("views", 0)} for p in top_properties]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
