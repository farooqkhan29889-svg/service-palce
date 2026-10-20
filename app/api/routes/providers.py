from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database, to_object_id
from app.core.serialization import to_jsonable
from app.core.dependencies import get_current_active_user, require_role
from app.models.schemas import ProviderCreate, ProviderUpdate
from app.core.time_utils import utcnow

router = APIRouter()

@router.post("/register", response_model=dict)
async def register_provider(
    provider: ProviderCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Register as a service provider"""
    db = get_database()

    # Check if already a provider
    existing = await db.providers.find_one({"user_id": str(current_user["_id"])})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already registered as a provider"
        )

    provider_dict = provider.dict()
    provider_dict["user_id"] = str(current_user["_id"])
    provider_dict["is_approved"] = False
    provider_dict["is_online"] = False
    provider_dict["rating"] = {"average": 0, "count": 0}
    provider_dict["total_jobs"] = 0
    provider_dict["completed_jobs"] = 0
    provider_dict["cancelled_jobs"] = 0
    provider_dict["earnings"] = {"total": 0, "this_month": 0, "platform_fees_paid": 0}
    provider_dict["created_at"] = utcnow()
    provider_dict["updated_at"] = utcnow()

    result = await db.providers.insert_one(provider_dict)

    # Update user role
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"role": "provider"}}
    )

    return {
        "success": True,
        "message": "Provider registration submitted for approval",
        "data": {"provider_id": str(result.inserted_id)}
    }

@router.get("/profile", response_model=dict)
async def get_provider_profile(
    current_user: dict = Depends(require_role("provider"))
):
    """Get provider profile"""
    db = get_database()

    provider = await db.providers.find_one({"user_id": str(current_user["_id"])})
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider profile not found"
        )

    # Get user info
    user = await db.users.find_one({"_id": current_user["_id"]})

    return {
        "success": True,
        "data": {
            "provider": to_jsonable(provider),
            "user": {
                "name": user["name"],
                "phone": user["phone"],
                "email": user.get("email")
            }
        }
    }

@router.put("/profile", response_model=dict)
async def update_provider_profile(
    update: ProviderUpdate,
    current_user: dict = Depends(require_role("provider"))
):
    """Update provider profile"""
    db = get_database()

    update_data = {k: v for k, v in update.dict().items() if v is not None}
    update_data["updated_at"] = utcnow()

    await db.providers.update_one(
        {"user_id": str(current_user["_id"])},
        {"$set": update_data}
    )

    return {
        "success": True,
        "message": "Profile updated successfully"
    }

@router.put("/toggle-online", response_model=dict)
async def toggle_online_status(
    current_user: dict = Depends(require_role("provider"))
):
    """Toggle online/offline status"""
    db = get_database()

    provider = await db.providers.find_one({"user_id": str(current_user["_id"])})
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider profile not found"
        )

    new_status = not provider.get("is_online", False)

    await db.providers.update_one(
        {"user_id": str(current_user["_id"])},
        {"$set": {"is_online": new_status}}
    )

    return {
        "success": True,
        "message": f"You are now {'online' if new_status else 'offline'}",
        "data": {"is_online": new_status}
    }

@router.get("/earnings", response_model=dict)
async def get_earnings(
    current_user: dict = Depends(require_role("provider"))
):
    """Get provider earnings"""
    db = get_database()

    provider = await db.providers.find_one({"user_id": str(current_user["_id"])})
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider profile not found"
        )

    return {
        "success": True,
        "data": provider.get("earnings", {})
    }

@router.get("/search", response_model=dict)
async def search_providers(
    service_id: str = None,
    lat: float = None,
    lng: float = None,
    radius: int = 10
):
    """Search providers by service and location"""
    db = get_database()

    query = {"is_approved": True, "is_online": True}

    if service_id:
        query["services"] = service_id

    # Location-based search
    if lat is not None and lng is not None:
        query["location"] = {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "$maxDistance": radius * 1000  # Convert km to meters
            }
        }

    providers = await db.providers.find(query).limit(20).to_list(20)

    # Get user info for each provider
    result = []
    for provider in providers:
        user = await db.users.find_one({"_id": to_object_id(provider["user_id"])})
        result.append({
            **provider,
            "user_name": user["name"],
            "user_phone": user["phone"]
        })

    return {
        "success": True,
        "count": len(result),
        "data": to_jsonable(result)
    }

@router.get("/{provider_id}", response_model=dict)
async def get_provider_by_id(provider_id: str):
    """Get provider by ID"""
    db = get_database()

    provider = await db.providers.find_one({"_id": to_object_id(provider_id)})
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )

    # Get user info
    user = await db.users.find_one({"_id": to_object_id(provider["user_id"])})

    return {
        "success": True,
        "data": to_jsonable({
            **provider,
            "user_name": user["name"],
            "user_phone": user["phone"]
        })
    }
