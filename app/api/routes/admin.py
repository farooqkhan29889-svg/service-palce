from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database, to_object_id
from app.core.serialization import to_jsonable
from app.core.dependencies import require_role
from datetime import timedelta

from app.core.time_utils import utcnow

router = APIRouter()

@router.get("/dashboard", response_model=dict)
async def admin_dashboard(current_user: dict = Depends(require_role("admin"))):
    """Get admin dashboard stats"""
    db = get_database()

    total_users = await db.users.count_documents({"role": "customer"})
    total_providers = await db.providers.count_documents({})
    approved_providers = await db.providers.count_documents({"is_approved": True})
    pending_providers = await db.providers.count_documents({"is_approved": False})
    total_bookings = await db.bookings.count_documents({})
    active_bookings = await db.bookings.count_documents({"status": {"$in": ["pending", "confirmed", "in_progress"]}})
    completed_bookings = await db.bookings.count_documents({"status": "completed"})

    # Revenue calculation
    payments = await db.payments.find({"status": "completed"}).to_list(10000)
    total_revenue = sum(p.get("commission", {}).get("platform_fee", 0) + p.get("commission", {}).get("gst", 0) for p in payments)
    total_gmv = sum(p.get("amount", {}).get("total_amount", 0) for p in payments)

    # Monthly stats
    month_start = utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_bookings = await db.bookings.count_documents({"created_at": {"$gte": month_start}})
    monthly_payments = await db.payments.find({
        "status": "completed",
        "created_at": {"$gte": month_start}
    }).to_list(10000)
    monthly_revenue = sum(p.get("commission", {}).get("platform_fee", 0) + p.get("commission", {}).get("gst", 0) for p in monthly_payments)

    return {
        "success": True,
        "data": {
            "users": {"total": total_users},
            "providers": {
                "total": total_providers,
                "approved": approved_providers,
                "pending": pending_providers
            },
            "bookings": {
                "total": total_bookings,
                "active": active_bookings,
                "completed": completed_bookings,
                "this_month": monthly_bookings
            },
            "revenue": {
                "total": total_revenue,
                "this_month": monthly_revenue,
                "total_gmv": total_gmv
            }
        }
    }

@router.get("/providers/pending", response_model=dict)
async def get_pending_providers(current_user: dict = Depends(require_role("admin"))):
    """Get pending provider approvals"""
    db = get_database()

    providers = await db.providers.find({"is_approved": False}).to_list(100)

    result = []
    for provider in providers:
        user = await db.users.find_one({"_id": to_object_id(provider["user_id"])})
        result.append({
            **provider,
            "user_name": user["name"] if user else "Unknown",
            "user_phone": user["phone"] if user else "Unknown"
        })

    return {
        "success": True,
        "count": len(result),
        "data": to_jsonable(result)
    }

@router.put("/providers/{provider_id}/approve", response_model=dict)
async def approve_provider(
    provider_id: str,
    current_user: dict = Depends(require_role("admin"))
):
    """Approve a provider"""
    db = get_database()

    oid = to_object_id(provider_id)
    result = await db.providers.update_one(
        {"_id": oid, "is_approved": False},
        {"$set": {"is_approved": True, "updated_at": utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found or already approved"
        )

    # Get provider for notification
    provider = await db.providers.find_one({"_id": oid})
    if provider:
        await db.notifications.insert_one({
            "user_id": provider["user_id"],
            "type": "provider_approved",
            "title": "Account Approved",
            "message": "Your provider account has been approved! You can now start receiving bookings.",
            "data": {"provider_id": str(oid)},
            "is_read": False,
            "created_at": utcnow()
        })

    return {
        "success": True,
        "message": "Provider approved successfully"
    }

@router.put("/providers/{provider_id}/reject", response_model=dict)
async def reject_provider(
    provider_id: str,
    reason: str = None,
    current_user: dict = Depends(require_role("admin"))
):
    """Reject a provider application"""
    db = get_database()

    oid = to_object_id(provider_id)
    provider = await db.providers.find_one({"_id": oid})
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )

    await db.providers.update_one(
        {"_id": oid},
        {"$set": {
            "is_approved": False,
            "is_rejected": True,
            "reject_reason": reason,
            "updated_at": utcnow()
        }}
    )

    await db.notifications.insert_one({
        "user_id": provider["user_id"],
        "type": "provider_rejected",
        "title": "Application Update",
        "message": "Your provider application was not approved. Please contact support for details.",
        "data": {"provider_id": str(oid)},
        "is_read": False,
        "created_at": utcnow()
    })

    return {
        "success": True,
        "message": "Provider rejected"
    }

@router.get("/bookings", response_model=dict)
async def get_all_bookings(
    status_filter: str = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_role("admin"))
):
    """Get all bookings (admin)"""
    db = get_database()

    query = {}
    if status_filter:
        query["status"] = status_filter

    bookings = await db.bookings.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    total = await db.bookings.count_documents(query)

    return {
        "success": True,
        "count": len(bookings),
        "total": total,
        "data": to_jsonable(bookings)
    }

@router.get("/revenue", response_model=dict)
async def get_revenue_report(
    days: int = 30,
    current_user: dict = Depends(require_role("admin"))
):
    """Get revenue report for the last N days"""
    db = get_database()

    start_date = utcnow() - timedelta(days=days)

    payments = await db.payments.find({
        "status": "completed",
        "created_at": {"$gte": start_date}
    }).to_list(10000)

    # Daily breakdown
    daily = {}
    for p in payments:
        day = p["created_at"].strftime("%Y-%m-%d") if hasattr(p["created_at"], "strftime") else str(p["created_at"])[:10]
        if day not in daily:
            daily[day] = {"bookings": 0, "gmv": 0, "platform_fee": 0, "gst": 0}
        daily[day]["bookings"] += 1
        daily[day]["gmv"] += p.get("amount", {}).get("total_amount", 0)
        daily[day]["platform_fee"] += p.get("commission", {}).get("platform_fee", 0)
        daily[day]["gst"] += p.get("commission", {}).get("gst", 0)

    total_gmv = sum(d["gmv"] for d in daily.values())
    total_platform_fee = sum(d["platform_fee"] for d in daily.values())
    total_gst = sum(d["gst"] for d in daily.values())

    return {
        "success": True,
        "data": {
            "period_days": days,
            "total_gmv": total_gmv,
            "total_platform_fee": total_platform_fee,
            "total_gst": total_gst,
            "total_revenue": total_platform_fee + total_gst,
            "daily_breakdown": daily
        }
    }
