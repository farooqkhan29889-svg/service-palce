from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database, to_object_id
from app.core.serialization import to_jsonable
from app.core.dependencies import get_current_active_user

router = APIRouter()

@router.get("/", response_model=dict)
async def get_notifications(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_active_user)
):
    """Get notifications for current user"""
    db = get_database()

    user_id = str(current_user["_id"])

    notifications = await db.notifications.find(
        {"user_id": user_id}
    ).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)

    unread_count = await db.notifications.count_documents({
        "user_id": user_id,
        "is_read": False
    })

    return {
        "success": True,
        "unread_count": unread_count,
        "data": to_jsonable(notifications)
    }

@router.put("/{notification_id}/read", response_model=dict)
async def mark_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Mark a notification as read"""
    db = get_database()

    result = await db.notifications.update_one(
        {"_id": to_object_id(notification_id), "user_id": str(current_user["_id"])},
        {"$set": {"is_read": True}}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    return {
        "success": True,
        "message": "Notification marked as read"
    }

@router.put("/read-all", response_model=dict)
async def mark_all_as_read(
    current_user: dict = Depends(get_current_active_user)
):
    """Mark all notifications as read"""
    db = get_database()

    await db.notifications.update_many(
        {"user_id": str(current_user["_id"]), "is_read": False},
        {"$set": {"is_read": True}}
    )

    return {
        "success": True,
        "message": "All notifications marked as read"
    }
