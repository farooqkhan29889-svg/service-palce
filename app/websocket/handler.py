from fastapi import WebSocket, WebSocketDisconnect
from app.core.database import get_database, to_object_id
from app.core.security import decode_access_token
from app.core.time_utils import utcnow
import json

# Store active connections: {user_id: websocket}
active_connections: dict[str, WebSocket] = {}


async def provider_doc_id(db, user_id):
    """Resolve a provider's document id from their user id."""
    provider = await db.providers.find_one({"user_id": str(user_id)})
    return str(provider["_id"]) if provider else None


async def booking_parties(db, booking):
    """Return (customer_user_id, provider_user_id) for a booking.

    A booking stores the provider *document* id, but WebSocket connections are
    keyed by user id, so the provider's user id has to be looked up.
    """
    customer_user_id = booking["customer_id"]
    provider = await db.providers.find_one({"_id": to_object_id(booking["provider_id"])})
    provider_user_id = provider["user_id"] if provider else booking["provider_id"]
    return customer_user_id, provider_user_id


async def find_booking(db, booking_id):
    """Look a booking up by document id, falling back to the reference id."""
    booking = await db.bookings.find_one({"_id": to_object_id(booking_id)})
    if not booking:
        booking = await db.bookings.find_one({"booking_id": booking_id})
    return booking


async def is_party(db, booking, user_id):
    """Check whether the connected user is a party to the booking.

    Without this check any authenticated user could inject chat messages or
    spoof location and status updates for a booking they are not part of.
    """
    customer_user_id, provider_user_id = await booking_parties(db, booking)
    return str(user_id) in (str(customer_user_id), str(provider_user_id))


async def websocket_endpoint(websocket: WebSocket, token: str = None):
    await websocket.accept()

    user_id = None
    if token:
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("sub")

    if not user_id:
        await websocket.send_json({"error": "Authentication required"})
        await websocket.close(code=4001)
        return

    active_connections[user_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "location_update":
                # Provider shares live location with customer
                booking_id = message.get("booking_id")
                lat = message.get("lat")
                lng = message.get("lng")

                if booking_id:
                    db = get_database()
                    booking = await find_booking(db, booking_id)
                    if booking:
                        if not await is_party(db, booking, user_id):
                            await websocket.send_json({
                                "type": "error",
                                "message": "Not a party to this booking"
                            })
                            continue
                        customer_user_id, _ = await booking_parties(db, booking)
                        if customer_user_id in active_connections:
                            await active_connections[customer_user_id].send_json({
                                "type": "provider_location",
                                "booking_id": str(booking["_id"]),
                                "lat": lat,
                                "lng": lng
                            })

            elif msg_type == "chat_message":
                # Real-time chat between customer and provider
                booking_id = message.get("booking_id")
                text = message.get("message")

                if booking_id and text:
                    db = get_database()
                    booking = await find_booking(db, booking_id)
                    if booking:
                        if not await is_party(db, booking, user_id):
                            await websocket.send_json({
                                "type": "error",
                                "message": "Not a party to this booking"
                            })
                            continue
                        chat_msg = {
                            "booking_id": str(booking["_id"]),
                            "sender_id": user_id,
                            "sender_name": message.get("sender_name", ""),
                            "message": text,
                            "created_at": utcnow().isoformat()
                        }

                        # Save to DB. Insert a copy: pymongo mutates the
                        # document it is given by adding an ObjectId _id, which
                        # would then break JSON encoding of the payload below.
                        await db.chat_messages.insert_one({**chat_msg})

                        # Send to the other party
                        customer_user_id, provider_user_id = await booking_parties(db, booking)
                        target_id = (
                            provider_user_id if user_id == customer_user_id
                            else customer_user_id
                        )
                        if target_id in active_connections:
                            await active_connections[target_id].send_json({
                                "type": "chat_message",
                                **chat_msg
                            })

                        # Acknowledge to sender
                        await websocket.send_json({
                            "type": "message_sent",
                            "booking_id": str(booking["_id"])
                        })

            elif msg_type == "booking_status":
                # Booking status update broadcast
                booking_id = message.get("booking_id")
                new_status = message.get("status")

                if booking_id and new_status:
                    db = get_database()
                    booking = await find_booking(db, booking_id)
                    if booking:
                        if not await is_party(db, booking, user_id):
                            await websocket.send_json({
                                "type": "error",
                                "message": "Not a party to this booking"
                            })
                            continue
                        customer_user_id, provider_user_id = await booking_parties(db, booking)
                        target_id = (
                            customer_user_id if user_id == provider_user_id
                            else provider_user_id
                        )
                        if target_id in active_connections:
                            await active_connections[target_id].send_json({
                                "type": "booking_status",
                                "booking_id": str(booking["_id"]),
                                "status": new_status
                            })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    finally:
        if user_id in active_connections:
            del active_connections[user_id]
