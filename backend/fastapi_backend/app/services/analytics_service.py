"""Analytics service for admin dashboard metrics."""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from bson import ObjectId
import logging

from app.core.database import get_db
from app.models import PaymentStatus, SubscriptionStatus, BookingStatus

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics and reporting."""
    
    def __init__(self, db):
        self.db = db
    
    async def get_dashboard_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard analytics.
        
        Returns:
            Analytics data including revenue, bookings, subscriptions, etc.
        """
        # Calculate date ranges
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        
        # Revenue analytics
        total_revenue = await self._calculate_total_revenue()
        monthly_revenue = await self._calculate_monthly_revenue()
        current_month_revenue = monthly_revenue.get(month_start.strftime("%Y-%m"), 0)
        
        # Booking analytics
        total_bookings = await self.db.bookings.count_documents({})
        completed_bookings = await self.db.bookings.count_documents({
            "status": BookingStatus.COMPLETED.value
        })
        pending_bookings = await self.db.bookings.count_documents({
            "status": BookingStatus.PENDING.value
        })
        
        # Subscription analytics
        active_subscriptions = await self.db.subscriptions.count_documents({
            "status": SubscriptionStatus.ACTIVE.value
        })
        total_subscriptions = await self.db.subscriptions.count_documents({})
        
        # Property analytics
        total_properties = await self.db.properties.count_documents({})
        active_properties = await self.db.properties.count_documents({
            "status": "active"
        })
        featured_properties = await self.db.properties.count_documents({
            "is_featured": True
        })
        
        # User analytics
        total_users = await self.db.users.count_documents({})
        total_agents = await self.db.users.count_documents({
            "role": "agent"
        })
        
        # Conversion rate
        conversion_rate = (completed_bookings / total_bookings * 100) if total_bookings > 0 else 0
        
        # Top performers
        top_agents = await self._get_top_agents()
        top_properties = await self._get_top_properties()
        
        return {
            "revenue": {
                "total": total_revenue,
                "current_month": current_month_revenue,
                "monthly": monthly_revenue
            },
            "bookings": {
                "total": total_bookings,
                "completed": completed_bookings,
                "pending": pending_bookings
            },
            "subscriptions": {
                "active": active_subscriptions,
                "total": total_subscriptions
            },
            "properties": {
                "total": total_properties,
                "active": active_properties,
                "featured": featured_properties
            },
            "users": {
                "total": total_users,
                "agents": total_agents
            },
            "conversion_rate": round(conversion_rate, 2),
            "top_agents": top_agents,
            "top_properties": top_properties
        }
    
    async def _calculate_total_revenue(self) -> float:
        """Calculate total revenue from all completed payments."""
        pipeline = [
            {
                "$match": {
                    "status": PaymentStatus.COMPLETED.value
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$amount"}
                }
            }
        ]
        
        result = await self.db.payments.aggregate(pipeline).to_list(length=1)
        return result[0]["total"] if result else 0.0
    
    async def _calculate_monthly_revenue(self) -> Dict[str, float]:
        """Calculate revenue grouped by month."""
        pipeline = [
            {
                "$match": {
                    "status": PaymentStatus.COMPLETED.value
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m",
                            "date": "$created_at"
                        }
                    },
                    "revenue": {"$sum": "$amount"}
                }
            },
            {
                "$sort": {"_id": -1}
            },
            {
                "$limit": 12  # Last 12 months
            }
        ]
        
        results = await self.db.payments.aggregate(pipeline).to_list(length=12)
        return {item["_id"]: item["revenue"] for item in results}
    
    async def _get_top_agents(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing agents by sales."""
        pipeline = [
            {
                "$match": {
                    "is_active": True
                }
            },
            {
                "$sort": {"total_sales": -1}
            },
            {
                "$limit": limit
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user"
                }
            },
            {
                "$unwind": "$user"
            },
            {
                "$project": {
                    "_id": 1,
                    "name": "$user.full_name",
                    "email": "$user.email",
                    "total_sales": 1,
                    "total_earnings": 1,
                    "rating": 1
                }
            }
        ]
        
        agents = await self.db.agents.aggregate(pipeline).to_list(length=limit)
        
        # Convert ObjectId to string
        for agent in agents:
            agent["id"] = str(agent.pop("_id"))
        
        return agents
    
    async def _get_top_properties(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top properties by views and bookings."""
        pipeline = [
            {
                "$match": {
                    "status": "active"
                }
            },
            {
                "$addFields": {
                    "score": {
                        "$add": [
                            {"$multiply": ["$views", 1]},
                            {"$multiply": ["$booking_count", 10]},
                            {"$multiply": ["$favorites_count", 5]}
                        ]
                    }
                }
            },
            {
                "$sort": {"score": -1}
            },
            {
                "$limit": limit
            },
            {
                "$project": {
                    "_id": 1,
                    "title": 1,
                    "price": 1,
                    "city": 1,
                    "views": 1,
                    "booking_count": 1,
                    "favorites_count": 1,
                    "score": 1
                }
            }
        ]
        
        properties = await self.db.properties.aggregate(pipeline).to_list(length=limit)
        
        # Convert ObjectId to string
        for prop in properties:
            prop["id"] = str(prop.pop("_id"))
        
        return properties
    
    async def get_revenue_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get revenue report for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Revenue report
        """
        pipeline = [
            {
                "$match": {
                    "status": PaymentStatus.COMPLETED.value,
                    "created_at": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }
            },
            {
                "$group": {
                    "_id": "$payment_method",
                    "total": {"$sum": "$amount"},
                    "count": {"$sum": 1}
                }
            }
        ]
        
        results = await self.db.payments.aggregate(pipeline).to_list(length=None)
        
        total_revenue = sum(item["total"] for item in results)
        total_transactions = sum(item["count"] for item in results)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_revenue": total_revenue,
            "total_transactions": total_transactions,
            "by_payment_method": results
        }


async def get_analytics_service(db=None):
    """Get analytics service instance."""
    if db is None:
        db = get_db()
    return AnalyticsService(db)
