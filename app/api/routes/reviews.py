from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database, to_object_id
from app.core.serialization import to_jsonable
from app.core.dependencies import get_current_active_user, require_role
from app.models.schemas import ReviewCreate
from app.core.time_utils import utcnow

router = APIRouter()

@router.post("/", response_model=dict)
async def create_review(
    review: ReviewCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Leave a review for a completed booking"""
    db = get_database()

    booking = await db.bookings.find_one({"_id": to_object_id(review.booking_id)})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if booking["customer_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the customer can leave a review"
        )

    if booking["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only review completed bookings"
        )

    # Check if already reviewed
    existing = await db.reviews.find_one({"booking_id": str(booking["_id"])})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review already submitted for this booking"
        )

    now = utcnow()
    review_dict = {
        "booking_id": str(booking["_id"]),
        "customer_id": str(current_user["_id"]),
        "provider_id": booking["provider_id"],
        "rating": review.rating,
        "review": review.review,
        "created_at": now
    }

    await db.reviews.insert_one(review_dict)

    # Update booking with rating
    await db.bookings.update_one(
        {"_id": booking["_id"]},
        {"$set": {
            "customer_rating": {
                "rating": review.rating,
                "review": review.review
            },
            "updated_at": now
        }}
    )

    # Recalculate provider average rating
    all_reviews = await db.reviews.find({"provider_id": booking["provider_id"]}).to_list(1000)
    if all_reviews:
        avg_rating = sum(r["rating"] for r in all_reviews) / len(all_reviews)
        await db.providers.update_one(
            {"_id": to_object_id(booking["provider_id"])},
            {"$set": {
                "rating": {
                    "average": round(avg_rating, 2),
                    "count": len(all_reviews)
                }
            }}
        )

    return {
        "success": True,
        "message": "Review submitted successfully"
    }

@router.get("/provider/{provider_id}", response_model=dict)
async def get_provider_reviews(
    provider_id: str,
    limit: int = 20,
    offset: int = 0
):
    """Get reviews for a provider"""
    db = get_database()

    provider_key = str(to_object_id(provider_id))

    reviews = await db.reviews.find(
        {"provider_id": provider_key}
    ).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)

    # Enrich with customer names
    result = []
    for review in reviews:
        customer = await db.users.find_one({"_id": to_object_id(review["customer_id"])})
        result.append({
            **review,
            "customer_name": customer["name"] if customer else "Anonymous"
        })

    total = await db.reviews.count_documents({"provider_id": provider_key})

    return {
        "success": True,
        "count": len(result),
        "total": total,
        "data": to_jsonable(result)
    }
