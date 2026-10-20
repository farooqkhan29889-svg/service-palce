"""WebSocket smoke test: auth, ping/pong, live location, chat."""
import asyncio
import json
import urllib.request

import websockets

BASE = "http://127.0.0.1:8000"
WS = "ws://127.0.0.1:8000/ws"
passed, failed = 0, 0


def login(phone, password):
    req = urllib.request.Request(
        BASE + "/api/auth/login",
        data=json.dumps({"phone": phone, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["data"]["token"]


def check(label, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failed += 1
        print(f"  FAIL  {label}  {detail}")


async def main():
    print("=" * 62)
    print("ServeNow WebSocket test")
    print("=" * 62)

    print("\n[1] Authentication")
    async with websockets.connect(WS) as ws:
        msg = json.loads(await ws.recv())
        check("rejects missing token", msg.get("error") == "Authentication required", msg)
    cust_token = login("9876543211", "customer123")
    prov_token = login("9123456781", "provider123")

    async with websockets.connect(f"{WS}?token={cust_token}") as cust_ws:
        async with websockets.connect(f"{WS}?token={prov_token}") as prov_ws:
            print("\n[2] Ping / pong")
            await cust_ws.send(json.dumps({"type": "ping"}))
            msg = json.loads(await cust_ws.recv())
            check("ping -> pong", msg.get("type") == "pong", msg)

            print("\n[3] Create a booking to talk about")
            # Use the provider's own profile rather than a geo search: search
            # results are ordered by distance, so they do not identify the
            # provider that is logged in below.
            req = urllib.request.Request(
                BASE + "/api/providers/profile",
                headers={"Authorization": f"Bearer {prov_token}"},
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                profile = json.loads(r.read())["data"]["provider"]
            provider_id = profile["_id"]
            service_id = profile["services"][0]

            req = urllib.request.Request(
                BASE + "/api/bookings/",
                data=json.dumps({
                    "provider_id": provider_id,
                    "service_id": service_id,
                    "service_date": "2026-11-05T10:00:00",
                    "service_time": "10:00 AM",
                    "address": "9 WS Lane",
                    "city": "Mumbai",
                }).encode(),
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {cust_token}"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                booking = json.loads(r.read())["data"]
            booking_id = booking["booking_id"]
            print(f"        booking={booking_id}")

            print("\n[4] Provider sends live location -> customer receives")
            await prov_ws.send(json.dumps({
                "type": "location_update",
                "booking_id": booking_id,
                "lat": 19.0760,
                "lng": 72.8777,
            }))
            msg = json.loads(await asyncio.wait_for(cust_ws.recv(), timeout=15))
            check("customer got provider_location",
                  msg.get("type") == "provider_location"
                  and msg.get("booking_id") == booking_id
                  and msg.get("lat") == 19.0760, msg)

            print("\n[5] Customer chats -> provider receives")
            await cust_ws.send(json.dumps({
                "type": "chat_message",
                "booking_id": booking_id,
                "message": "Please come after 6 PM",
                "sender_name": "Customer 2",
            }))
            msg = json.loads(await asyncio.wait_for(prov_ws.recv(), timeout=15))
            check("provider got chat_message",
                  msg.get("type") == "chat_message"
                  and msg.get("message") == "Please come after 6 PM", msg)

            ack = json.loads(await asyncio.wait_for(cust_ws.recv(), timeout=15))
            check("sender got message_sent ack",
                  ack.get("type") == "message_sent", ack)

            print("\n[6] Provider broadcasts status -> customer receives")
            await prov_ws.send(json.dumps({
                "type": "booking_status",
                "booking_id": booking_id,
                "status": "on_the_way",
            }))
            msg = json.loads(await asyncio.wait_for(cust_ws.recv(), timeout=15))
            check("customer got booking_status",
                  msg.get("type") == "booking_status"
                  and msg.get("status") == "on_the_way", msg)

            print("\n[7] A user who is not a party to the booking is rejected")
            other_token = login("9876543212", "customer123")
            async with websockets.connect(f"{WS}?token={other_token}") as other_ws:
                await other_ws.send(json.dumps({
                    "type": "chat_message",
                    "booking_id": booking_id,
                    "message": "I am not part of this booking",
                }))
                msg = json.loads(await asyncio.wait_for(other_ws.recv(), timeout=15))
                check("non-party rejected",
                      msg.get("type") == "error", msg)

    print("\n" + "=" * 62)
    print(f"RESULT: {passed} passed, {failed} failed")
    print("=" * 62)
    raise SystemExit(1 if failed else 0)


asyncio.run(main())
