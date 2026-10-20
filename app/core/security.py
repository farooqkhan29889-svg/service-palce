from datetime import timedelta

from app.core.time_utils import utcnow
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from app.core.config import settings

# bcrypt only reads the first 72 bytes of a password. Longer inputs are
# rejected by newer bcrypt releases, so truncate explicitly and consistently.
BCRYPT_MAX_BYTES = 72


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:BCRYPT_MAX_BYTES]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    try:
        return bcrypt.checkpw(_encode(plain_password), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt()).decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = utcnow() + expires_delta
    else:
        expire = utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode JWT access token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def calculate_pricing(service_charge: float) -> dict:
    """Calculate pricing with 10% platform fee"""
    platform_fee = round(service_charge * settings.PLATFORM_COMMISSION_RATE)
    gst = round(platform_fee * settings.GST_RATE)
    total_amount = service_charge + gst
    provider_earnings = service_charge - platform_fee

    return {
        "service_charge": service_charge,
        "platform_fee": platform_fee,
        "platform_fee_percentage": settings.PLATFORM_COMMISSION_RATE * 100,
        "gst": gst,
        "gst_percentage": settings.GST_RATE * 100,
        "total_amount": total_amount,
        "provider_earnings": provider_earnings
    }
