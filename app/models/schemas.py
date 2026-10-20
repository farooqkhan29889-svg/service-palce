from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

from app.core.time_utils import utcnow

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# User Models
class UserBase(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    role: str = "customer"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None

class UserInDB(UserBase):
    id: str = Field(alias="_id")
    password: str
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class UserResponse(UserBase):
    id: str = Field(alias="_id")
    is_verified: bool
    created_at: datetime

    class Config:
        populate_by_name = True

# Address Models
class Address(BaseModel):
    type: str = "home"
    label: Optional[str] = None
    address: str
    city: str
    state: str
    pincode: str
    coordinates: Optional[dict] = None
    is_default: bool = False

# Wallet Models
class WalletTransaction(BaseModel):
    type: str
    amount: float
    description: str
    booking_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)

class Wallet(BaseModel):
    balance: float = 0.0
    transactions: List[WalletTransaction] = []

# Provider Models
class ProviderBase(BaseModel):
    user_id: str
    services: List[str]
    experience_years: int
    aadhaar_number: str
    daily_wage: float
    skills: List[str] = []

class ProviderCreate(ProviderBase):
    pass

class ProviderUpdate(BaseModel):
    services: Optional[List[str]] = None
    experience_years: Optional[int] = None
    daily_wage: Optional[float] = None
    skills: Optional[List[str]] = None
    is_online: Optional[bool] = None

class ProviderInDB(ProviderBase):
    id: str = Field(alias="_id")
    is_approved: bool = False
    is_online: bool = False
    rating: dict = {"average": 0, "count": 0}
    total_jobs: int = 0
    completed_jobs: int = 0
    cancelled_jobs: int = 0
    earnings: dict = {"total": 0, "this_month": 0, "platform_fees_paid": 0}
    location: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class ProviderResponse(ProviderBase):
    id: str = Field(alias="_id")
    is_approved: bool
    is_online: bool
    rating: dict
    total_jobs: int
    completed_jobs: int

    class Config:
        populate_by_name = True

# Service Models
class ServiceBase(BaseModel):
    name: str
    icon: str
    description: str
    category: str
    base_price: float
    duration: int = 60

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None
    is_active: Optional[bool] = None

class ServiceInDB(ServiceBase):
    id: str = Field(alias="_id")
    slug: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class ServiceResponse(ServiceBase):
    id: str = Field(alias="_id")
    slug: str
    is_active: bool

    class Config:
        populate_by_name = True

# Booking Models
class BookingBase(BaseModel):
    customer_id: str
    provider_id: str
    service_id: str
    service_date: datetime
    service_time: str
    address: str
    city: str
    coordinates: Optional[dict] = None
    issue_description: Optional[str] = None

class BookingCreate(BaseModel):
    provider_id: str
    service_id: str
    service_date: datetime
    service_time: str
    address: str
    city: str
    coordinates: Optional[dict] = None
    issue_description: Optional[str] = None
    payment_method: str = "upi"

class BookingInDB(BookingBase):
    id: str = Field(alias="_id")
    booking_id: str
    pricing: dict
    payment: dict
    status: str = "pending"
    timeline: dict
    provider_location: Optional[dict] = None
    customer_rating: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class BookingResponse(BookingBase):
    id: str = Field(alias="_id")
    booking_id: str
    pricing: dict
    status: str
    payment: dict

    class Config:
        populate_by_name = True

# Payment Models
class PaymentBase(BaseModel):
    booking_id: str
    customer_id: str
    provider_id: str
    amount: dict
    method: str
    gateway: str

class PaymentInDB(PaymentBase):
    id: str = Field(alias="_id")
    status: str = "created"
    gateway_order_id: Optional[str] = None
    gateway_payment_id: Optional[str] = None
    commission: dict
    provider_payout: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class PaymentResponse(PaymentBase):
    id: str = Field(alias="_id")
    status: str

    class Config:
        populate_by_name = True

# Review Models
class ReviewBase(BaseModel):
    booking_id: str
    customer_id: str
    provider_id: str
    rating: int = Field(ge=1, le=5)
    review: Optional[str] = None

class ReviewCreate(BaseModel):
    booking_id: str
    rating: int = Field(ge=1, le=5)
    review: Optional[str] = None

class ReviewInDB(ReviewBase):
    id: str = Field(alias="_id")
    created_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class ReviewResponse(ReviewBase):
    id: str = Field(alias="_id")
    created_at: datetime

    class Config:
        populate_by_name = True

# Notification Models
class NotificationBase(BaseModel):
    user_id: str
    type: str
    title: str
    message: str
    data: Optional[dict] = None

class NotificationInDB(NotificationBase):
    id: str = Field(alias="_id")
    is_read: bool = False
    created_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class NotificationResponse(NotificationBase):
    id: str = Field(alias="_id")
    is_read: bool
    created_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

# Auth Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    phone: str
    password: str

class OTPRequest(BaseModel):
    phone: str

class OTPVerify(BaseModel):
    phone: str
    otp: str
