from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database, to_object_id
from app.core.config import settings
from app.core.dependencies import get_current_active_user
from app.core.time_utils import utcnow
import razorpay
import hmac
import hashlib

router = APIRouter()

def get_razorpay_client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return None
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@router.post("/create-order", response_model=dict)
async def create_payment_order(
    booking_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a Razorpay payment order for a booking"""
    db = get_database()

    booking = await db.bookings.find_one({"_id": to_object_id(booking_id)})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if booking["customer_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your booking"
        )

    pricing = booking["pricing"]
    amount_paise = int(pricing["total_amount"] * 100)

    client = get_razorpay_client()
    gateway_order_id = None

    if client:
        try:
            order = client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "receipt": booking["booking_id"],
                "notes": {
                    "booking_id": str(booking["_id"]),
                    "customer_id": str(current_user["_id"]),
                    "provider_id": booking["provider_id"]
                }
            })
            gateway_order_id = order["id"]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Payment gateway error: {str(e)}"
            )
    else:
        # Demo mode — no Razorpay keys configured
        gateway_order_id = f"demo_order_{booking['booking_id']}"

    now = utcnow()

    # Create payment record
    payment_record = {
        "booking_id": str(booking["_id"]),
        "customer_id": str(current_user["_id"]),
        "provider_id": booking["provider_id"],
        "amount": pricing,
        "method": booking["payment"].get("method", "upi"),
        "gateway": "razorpay" if client else "demo",
        "status": "created",
        "gateway_order_id": gateway_order_id,
        "gateway_payment_id": None,
        "commission": {
            "platform_fee": pricing["platform_fee"],
            "gst": pricing["gst"]
        },
        "provider_payout": {
            "amount": pricing["provider_earnings"],
            "status": "pending"
        },
        "created_at": now,
        "updated_at": now
    }

    result = await db.payments.insert_one(payment_record)

    return {
        "success": True,
        "data": {
            "payment_id": str(result.inserted_id),
            "order_id": gateway_order_id,
            "amount": amount_paise,
            "currency": "INR",
            "razorpay_key": settings.RAZORPAY_KEY_ID or "demo_key",
            "pricing": pricing
        }
    }

@router.post("/verify", response_model=dict)
async def verify_payment(
    booking_id: str,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Verify Razorpay payment signature"""
    db = get_database()

    payment = await db.payments.find_one({
        "booking_id": str(to_object_id(booking_id)),
        "gateway_order_id": razorpay_order_id
    })

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found"
        )

    # Verify signature
    client = get_razorpay_client()
    if client:
        try:
            body = f"{razorpay_order_id}|{razorpay_payment_id}"
            expected_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()

            if expected_signature != razorpay_signature:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment verification failed — invalid signature"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Verification error: {str(e)}"
            )

    now = utcnow()
    await db.payments.update_one(
        {"_id": payment["_id"]},
        {"$set": {
            "status": "completed",
            "gateway_payment_id": razorpay_payment_id,
            "provider_payout.status": "processed",
            "updated_at": now
        }}
    )

    # Update booking payment status
    await db.bookings.update_one(
        {"_id": to_object_id(booking_id)},
        {"$set": {
            "payment.status": "completed",
            "payment.transaction_id": razorpay_payment_id,
            "updated_at": now
        }}
    )

    return {
        "success": True,
        "message": "Payment verified successfully"
    }

@router.get("/status/{booking_id}", response_model=dict)
async def get_payment_status(
    booking_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get payment status for a booking"""
    db = get_database()

    payment = await db.payments.find_one({"booking_id": str(to_object_id(booking_id))})
    if not payment:
        return {
            "success": True,
            "data": {"status": "no_payment", "message": "No payment record found"}
        }

    return {
        "success": True,
        "data": {
            "payment_id": str(payment["_id"]),
            "status": payment["status"],
            "amount": payment["amount"],
            "method": payment["method"],
            "gateway": payment["gateway"],
            "commission": payment["commission"],
            "provider_payout": payment["provider_payout"]
        }
    }

@router.post("/refund/{booking_id}", response_model=dict)
async def refund_payment(
    booking_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Initiate refund for a cancelled booking (admin or customer)"""
    db = get_database()

    payment = await db.payments.find_one({
        "booking_id": str(to_object_id(booking_id)),
        "status": "completed"
    })
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed payment found for this booking"
        )

    user_id = str(current_user["_id"])
    if payment["customer_id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    client = get_razorpay_client()
    if client and payment.get("gateway_payment_id"):
        try:
            client.payment.refund(payment["gateway_payment_id"], {
                "amount": int(payment["amount"]["total_amount"] * 100)
            })
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Refund error: {str(e)}"
            )

    now = utcnow()
    await db.payments.update_one(
        {"_id": payment["_id"]},
        {"$set": {
            "status": "refunded",
            "provider_payout.status": "reversed",
            "updated_at": now
        }}
    )

    return {
        "success": True,
        "message": "Refund initiated successfully"
    }
