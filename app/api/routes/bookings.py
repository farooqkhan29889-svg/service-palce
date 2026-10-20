from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database, to_object_id
from app.core.serialization import to_jsonable
from app.core.security import calculate_pricing
from app.core.dependencies import get_current_active_user, require_role
from app.models.schemas import BookingCreate
from app.core.time_utils import utcnow
import random
import string

router = APIRouter()

def generate_booking_id() -> str:
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(random.choices(chars, k=8))
    return f"SN-{suffix}"


async def provider_doc_id(db, user_id):
    """Resolve a provider's document id from their user id.

    A booking stores the provider *document* id, but an authenticated provider
    only knows their *user* id, so every provider-side check has to translate.
    """
    provider = await db.providers.find_one({"user_id": str(user_id)})
    return str(provider["_id"]) if provider else None

@router.post("/", response_model=dict)
async def create_booking(
    booking: BookingCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new booking"""
    db = get_database()

    # Verify service exists
    service = await db.services.find_one({"_id": to_object_id(booking.service_id), "is_active": True})
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or inactive"
        )

    # Verify provider exists and is approved. The client may send either the
    # provider document id (from /api/providers/search) or the provider's user
    # id (from login), so accept both.
    provider = await db.providers.find_one({
        "_id": to_object_id(booking.provider_id),
        "is_approved": True
    })
    if not provider:
        provider = await db.providers.find_one({
            "user_id": str(booking.provider_id),
            "is_approved": True
        })
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found or not approved"
        )

    # Calculate pricing with 10% commission
    pricing = calculate_pricing(service["base_price"])

    now = utcnow()
    booking_id = generate_booking_id()

    booking_dict = {
        "booking_id": booking_id,
        "customer_id": str(current_user["_id"]),
        "provider_id": str(provider["_id"]),
        "service_id": str(service["_id"]),
        "service_name": service["name"],
        "service_date": booking.service_date,
        "service_time": booking.service_time,
        "address": booking.address,
        "city": booking.city,
        "coordinates": booking.coordinates,
        "issue_description": booking.issue_description,
        "pricing": pricing,
        "payment": {
            "method": booking.payment_method,
            "status": "pending",
            "amount": pricing["total_amount"]
        },
        "status": "pending",
        "timeline": {
            "created_at": now.isoformat(),
            "confirmed_at": None,
            "started_at": None,
            "completed_at": None,
            "cancelled_at": None
        },
        "provider_location": None,
        "customer_rating": None,
        "created_at": now,
        "updated_at": now
    }

    result = await db.bookings.insert_one(booking_dict)

    # Create notification for provider (addressed to the provider's user account)
    await db.notifications.insert_one({
        "user_id": provider["user_id"],
        "type": "new_booking",
        "title": "New Booking Request",
        "message": f"You have a new booking request for {service['name']}",
        "data": {"booking_id": str(result.inserted_id)},
        "is_read": False,
        "created_at": now
    })

    return {
        "success": True,
        "message": "Booking created successfully",
        "data": {
            "booking_id": str(result.inserted_id),
            "booking_ref": booking_id,
            "pricing": pricing
        }
    }

@router.get("/", response_model=dict)
async def get_bookings(
    status_filter: str = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Get bookings for current user (customer or provider)"""
    db = get_database()

    user_id = str(current_user["_id"])
    role = current_user["role"]

    if role == "customer":
        query = {"customer_id": user_id}
    elif role == "provider":
        # Bookings reference the provider document, so resolve it from the user id
        provider = await db.providers.find_one({"user_id": user_id})
        if not provider:
            return {"success": True, "count": 0, "data": []}
        query = {"provider_id": str(provider["_id"])}
    else:
        return {"success": True, "data": []}

    if status_filter:
        query["status"] = status_filter

    bookings = await db.bookings.find(query).sort("created_at", -1).to_list(100)

    return {
        "success": True,
        "count": len(bookings),
        "data": to_jsonable(bookings)
    }

@router.get("/{booking_id}", response_model=dict)
async def get_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get booking details"""
    db = get_database()

    oid = to_object_id(booking_id)
    booking = await db.bookings.find_one({"_id": oid})
    if not booking:
        # Fall back to the human-readable reference (e.g. SN-A1B2C3D4)
        booking = await db.bookings.find_one({"booking_id": booking_id})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    user_id = str(current_user["_id"])
    is_customer = booking["customer_id"] == user_id
    is_provider = booking["provider_id"] == await provider_doc_id(db, user_id)
    if not is_customer and not is_provider and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this booking"
        )

    # Enrich with service and user info
    service = await db.services.find_one({"_id": to_object_id(booking["service_id"])})
    customer = await db.users.find_one({"_id": to_object_id(booking["customer_id"])})
    provider = await db.users.find_one({"_id": to_object_id(booking["provider_id"])})

    return {
        "success": True,
        "data": to_jsonable({
            **booking,
            "service_info": {"name": service["name"], "category": service["category"]} if service else None,
            "customer_info": {"name": customer["name"], "phone": customer["phone"]} if customer else None,
            "provider_info": {"name": provider["name"], "phone": provider["phone"]} if provider else None
        })
    }

@router.put("/{booking_id}/confirm", response_model=dict)
async def confirm_booking(
    booking_id: str,
    current_user: dict = Depends(require_role("provider"))
):
    """Provider confirms a booking"""
    db = get_database()

    booking = await db.bookings.find_one({"_id": to_object_id(booking_id)})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if booking["provider_id"] != await provider_doc_id(db, current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your booking"
        )

    if booking["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm booking with status '{booking['status']}'"
        )

    now = utcnow()
    await db.bookings.update_one(
        {"_id": booking["_id"]},
        {"$set": {
            "status": "confirmed",
            "timeline.confirmed_at": now.isoformat(),
            "updated_at": now
        }}
    )

    # Notify customer
    await db.notifications.insert_one({
        "user_id": booking["customer_id"],
        "type": "booking_confirmed",
        "title": "Booking Confirmed",
        "message": f"Your booking {booking['booking_id']} has been confirmed",
        "data": {"booking_id": str(booking["_id"])},
        "is_read": False,
        "created_at": now
    })

    return {
        "success": True,
        "message": "Booking confirmed"
    }

@router.put("/{booking_id}/start", response_model=dict)
async def start_booking(
    booking_id: str,
    current_user: dict = Depends(require_role("provider"))
):
    """Provider starts the service"""
    db = get_database()

    booking = await db.bookings.find_one({"_id": to_object_id(booking_id)})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if booking["provider_id"] != await provider_doc_id(db, current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your booking"
        )

    if booking["status"] != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start booking with status '{booking['status']}'"
        )

    now = utcnow()
    await db.bookings.update_one(
        {"_id": booking["_id"]},
        {"$set": {
            "status": "in_progress",
            "timeline.started_at": now.isoformat(),
            "updated_at": now
        }}
    )

    # Notify customer
    await db.notifications.insert_one({
        "user_id": booking["customer_id"],
        "type": "service_started",
        "title": "Service Started",
        "message": "Your service provider has started the work",
        "data": {"booking_id": str(booking["_id"])},
        "is_read": False,
        "created_at": now
    })

    return {
        "success": True,
        "message": "Service started"
    }

@router.put("/{booking_id}/complete", response_model=dict)
async def complete_booking(
    booking_id: str,
    current_user: dict = Depends(require_role("provider"))
):
    """Provider completes the service"""
    db = get_database()

    booking = await db.bookings.find_one({"_id": to_object_id(booking_id)})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if booking["provider_id"] != await provider_doc_id(db, current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your booking"
        )

    if booking["status"] != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete booking with status '{booking['status']}'"
        )

    now = utcnow()
    pricing = booking["pricing"]

    await db.bookings.update_one(
        {"_id": booking["_id"]},
        {"$set": {
            "status": "completed",
            "timeline.completed_at": now.isoformat(),
            "payment.status": "completed",
            "updated_at": now
        }}
    )

    # Update provider stats
    provider_earning = pricing["provider_earnings"]
    await db.providers.update_one(
        {"_id": to_object_id(booking["provider_id"])},
        {
            "$inc": {
                "completed_jobs": 1,
                "total_jobs": 1,
                "earnings.total": provider_earning,
                "earnings.this_month": provider_earning,
                "earnings.platform_fees_paid": pricing["platform_fee"]
            }
        }
    )

    # Notify customer
    await db.notifications.insert_one({
        "user_id": booking["customer_id"],
        "type": "service_completed",
        "title": "Service Completed",
        "message": f"Your service is complete. Amount: Rs.{pricing['total_amount']}",
        "data": {"booking_id": str(booking["_id"]), "amount": pricing["total_amount"]},
        "is_read": False,
        "created_at": now
    })

    return {
        "success": True,
        "message": "Service completed",
        "data": {"pricing": pricing}
    }

@router.put("/{booking_id}/cancel", response_model=dict)
async def cancel_booking(
    booking_id: str,
    reason: str = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Cancel a booking (customer or provider)"""
    db = get_database()

    booking = await db.bookings.find_one({"_id": to_object_id(booking_id)})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    user_id = str(current_user["_id"])
    is_customer = booking["customer_id"] == user_id
    is_provider = booking["provider_id"] == await provider_doc_id(db, user_id)
    if not is_customer and not is_provider:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this booking"
        )

    if booking["status"] in ("completed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel booking with status '{booking['status']}'"
        )

    now = utcnow()
    await db.bookings.update_one(
        {"_id": booking["_id"]},
        {"$set": {
            "status": "cancelled",
            "timeline.cancelled_at": now.isoformat(),
            "cancel_reason": reason,
            "cancelled_by": user_id,
            "updated_at": now
        }}
    )

    # Update provider cancelled count
    if booking["provider_id"]:
        await db.providers.update_one(
            {"_id": to_object_id(booking["provider_id"])},
            {"$inc": {"cancelled_jobs": 1, "total_jobs": 1}}
        )

    # Notify the other party
    if is_customer:
        provider = await db.providers.find_one({"_id": to_object_id(booking["provider_id"])})
        other_user_id = provider["user_id"] if provider else booking["provider_id"]
    else:
        other_user_id = booking["customer_id"]
    await db.notifications.insert_one({
        "user_id": other_user_id,
        "type": "booking_cancelled",
        "title": "Booking Cancelled",
        "message": f"Booking {booking['booking_id']} has been cancelled",
        "data": {"booking_id": str(booking["_id"])},
        "is_read": False,
        "created_at": now
    })

    return {
        "success": True,
        "message": "Booking cancelled"
    }

@router.put("/{booking_id}/location", response_model=dict)
async def update_provider_location(
    booking_id: str,
    lat: float,
    lng: float,
    current_user: dict = Depends(require_role("provider"))
):
    """Provider updates live location during a booking"""
    db = get_database()

    booking = await db.bookings.find_one({"_id": to_object_id(booking_id)})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if booking["provider_id"] != await provider_doc_id(db, current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your booking"
        )

    await db.bookings.update_one(
        {"_id": booking["_id"]},
        {"$set": {
            "provider_location": {
                "type": "Point",
                "coordinates": [lng, lat]
            }
        }}
    )

    return {
        "success": True,
        "message": "Location updated"
    }
