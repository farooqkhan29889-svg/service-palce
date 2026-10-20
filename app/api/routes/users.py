from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database
from app.core.serialization import to_jsonable
from app.core.dependencies import get_current_active_user
from app.models.schemas import Address
from datetime import datetime

from app.core.time_utils import utcnow

router = APIRouter()

@router.get("/addresses", response_model=dict)
async def get_addresses(current_user: dict = Depends(get_current_active_user)):
    """Get user addresses"""
    return {
        "success": True,
        "data": to_jsonable(current_user.get("addresses", []))
    }

@router.post("/addresses", response_model=dict)
async def add_address(
    address: Address,
    current_user: dict = Depends(get_current_active_user)
):
    """Add new address"""
    db = get_database()

    # If this is default, unset other defaults
    if address.is_default:
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": {f"addresses.$[elem].is_default": False}},
            array_filters=[{"elem.is_default": True}]
        )

    address_dict = address.dict()
    address_dict["created_at"] = utcnow()

    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$push": {"addresses": address_dict}}
    )

    return {
        "success": True,
        "message": "Address added successfully"
    }

@router.get("/wallet", response_model=dict)
async def get_wallet(current_user: dict = Depends(get_current_active_user)):
    """Get wallet balance and transactions"""
    wallet = current_user.get("wallet", {"balance": 0.0, "transactions": []})

    return {
        "success": True,
        "data": to_jsonable({
            "balance": wallet.get("balance", 0.0),
            "transactions": sorted(
                wallet.get("transactions", []),
                key=lambda x: x.get("created_at", datetime.min),
                reverse=True
            )
        })
    }

@router.put("/fcm-token", response_model=dict)
async def update_fcm_token(
    fcm_token: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Update FCM token for push notifications"""
    db = get_database()

    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"fcm_token": fcm_token}}
    )

    return {
        "success": True,
        "message": "FCM token updated"
    }
