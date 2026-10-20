from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database, to_object_id
from app.core.serialization import to_jsonable
from app.core.dependencies import get_current_active_user, require_role
from app.models.schemas import ServiceCreate, ServiceUpdate
from app.core.time_utils import utcnow
import re

router = APIRouter()

def generate_slug(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")

@router.post("/", response_model=dict)
async def create_service(
    service: ServiceCreate,
    current_user: dict = Depends(require_role("admin"))
):
    """Create a new service (admin only)"""
    db = get_database()

    slug = generate_slug(service.name)
    existing = await db.services.find_one({"slug": slug})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service with this name already exists"
        )

    service_dict = service.dict()
    service_dict["slug"] = slug
    service_dict["is_active"] = True
    service_dict["created_at"] = utcnow()
    service_dict["updated_at"] = utcnow()

    result = await db.services.insert_one(service_dict)

    return {
        "success": True,
        "message": "Service created successfully",
        "data": {"service_id": str(result.inserted_id)}
    }

@router.get("/", response_model=dict)
async def get_services(category: str = None, is_active: bool = True):
    """Get all active services, optionally filtered by category"""
    db = get_database()

    query = {}
    if category:
        query["category"] = category
    if is_active is not None:
        query["is_active"] = is_active

    services = await db.services.find(query).to_list(100)

    return {
        "success": True,
        "count": len(services),
        "data": to_jsonable(services)
    }

@router.get("/categories", response_model=dict)
async def get_categories():
    """Get all unique service categories"""
    db = get_database()

    categories = await db.services.distinct("category", {"is_active": True})

    return {
        "success": True,
        "data": categories
    }

@router.get("/{service_id}", response_model=dict)
async def get_service(service_id: str):
    """Get a service by ID"""
    db = get_database()

    service = await db.services.find_one({"_id": to_object_id(service_id)})
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    return {
        "success": True,
        "data": to_jsonable(service)
    }

@router.put("/{service_id}", response_model=dict)
async def update_service(
    service_id: str,
    update: ServiceUpdate,
    current_user: dict = Depends(require_role("admin"))
):
    """Update a service (admin only)"""
    db = get_database()

    update_data = {k: v for k, v in update.dict().items() if v is not None}
    update_data["updated_at"] = utcnow()

    if "name" in update_data:
        update_data["slug"] = generate_slug(update_data["name"])

    result = await db.services.update_one(
        {"_id": to_object_id(service_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    return {
        "success": True,
        "message": "Service updated successfully"
    }

@router.delete("/{service_id}", response_model=dict)
async def delete_service(
    service_id: str,
    current_user: dict = Depends(require_role("admin"))
):
    """Soft-delete a service (admin only)"""
    db = get_database()

    result = await db.services.update_one(
        {"_id": to_object_id(service_id)},
        {"$set": {"is_active": False, "updated_at": utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    return {
        "success": True,
        "message": "Service deactivated successfully"
    }
