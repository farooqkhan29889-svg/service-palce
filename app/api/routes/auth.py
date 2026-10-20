from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token
)
from app.core.dependencies import get_current_active_user
from app.core.serialization import to_jsonable
from app.models.schemas import UserCreate, LoginRequest, Token
from datetime import timedelta

from app.core.time_utils import utcnow
import random

router = APIRouter()

@router.post("/register", response_model=dict)
async def register(user: UserCreate):
    """Register a new user"""
    db = get_database()

    # Check if user exists
    existing_user = await db.users.find_one({"phone": user.phone})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )

    # Create user
    user_dict = {
        "name": user.name,
        "phone": user.phone,
        "email": user.email,
        "password": get_password_hash(user.password),
        "role": user.role,
        "is_verified": False,
        "addresses": [],
        "wallet": {"balance": 0.0, "transactions": []},
        "created_at": utcnow(),
        "updated_at": utcnow()
    }

    result = await db.users.insert_one(user_dict)

    # Create token
    access_token = create_access_token(data={"sub": str(result.inserted_id)})

    return {
        "success": True,
        "message": "User registered successfully",
        "data": {
            "token": access_token,
            "user": {
                "id": str(result.inserted_id),
                "name": user.name,
                "phone": user.phone,
                "role": user.role
            }
        }
    }

@router.post("/login", response_model=dict)
async def login(credentials: LoginRequest):
    """Login user"""
    db = get_database()

    # Find user
    user = await db.users.find_one({"phone": credentials.phone})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verify password
    if not verify_password(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Create token
    access_token = create_access_token(data={"sub": str(user["_id"])})

    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "token": access_token,
            "user": {
                "id": str(user["_id"]),
                "name": user["name"],
                "phone": user["phone"],
                "role": user["role"]
            }
        }
    }

@router.post("/send-otp", response_model=dict)
async def send_otp(phone: str):
    """Send OTP to phone number"""
    db = get_database()

    # Generate OTP
    otp = str(random.randint(100000, 999999))
    otp_expiry = utcnow() + timedelta(minutes=10)

    # Update user with OTP
    await db.users.update_one(
        {"phone": phone},
        {"$set": {"otp": {"code": otp, "expires_at": otp_expiry}}}
    )

    # TODO: Send OTP via SMS (integrate with SMS gateway)
    print(f"OTP for {phone}: {otp}")

    return {
        "success": True,
        "message": "OTP sent successfully",
        "data": {"otp": otp}  # Remove in production
    }

@router.post("/verify-otp", response_model=dict)
async def verify_otp(phone: str, otp: str):
    """Verify OTP"""
    db = get_database()

    user = await db.users.find_one({"phone": phone})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    stored_otp = user.get("otp", {})
    if not stored_otp or stored_otp.get("code") != otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )

    if stored_otp.get("expires_at") < utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired"
        )

    # Mark user as verified
    await db.users.update_one(
        {"phone": phone},
        {"$set": {"is_verified": True}, "$unset": {"otp": ""}}
    )

    # Create token
    access_token = create_access_token(data={"sub": str(user["_id"])})

    return {
        "success": True,
        "message": "OTP verified successfully",
        "data": {
            "token": access_token,
            "user": {
                "id": str(user["_id"]),
                "name": user["name"],
                "phone": user["phone"]
            }
        }
    }

@router.get("/me", response_model=dict)
async def get_me(current_user: dict = Depends(get_current_active_user)):
    """Get current user profile"""
    return {
        "success": True,
        "data": {
            "user": to_jsonable({
                "id": str(current_user["_id"]),
                "name": current_user["name"],
                "phone": current_user["phone"],
                "email": current_user.get("email"),
                "role": current_user["role"],
                "is_verified": current_user["is_verified"],
                "addresses": current_user.get("addresses", []),
                "wallet": current_user.get("wallet", {}),
                "created_at": current_user["created_at"]
            })
        }
    }

@router.put("/profile", response_model=dict)
async def update_profile(
    name: str = None,
    email: str = None,
    avatar: str = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Update user profile"""
    db = get_database()

    update_data = {}
    if name:
        update_data["name"] = name
    if email:
        update_data["email"] = email
    if avatar:
        update_data["avatar"] = avatar

    update_data["updated_at"] = utcnow()

    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": update_data}
    )

    return {
        "success": True,
        "message": "Profile updated successfully"
    }
