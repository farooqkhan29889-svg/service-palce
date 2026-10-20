"""End-to-end smoke test against a running ServeNow API."""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"
passed, failed = 0, 0


def call(method, path, body=None, token=None, expect=200):
    global passed, failed
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            code, payload = r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        code, payload = e.code, json.loads(e.read() or b"{}")
    except Exception as e:
        code, payload = 0, {"error": str(e)}

    ok = code == expect
    if ok:
        passed += 1
        print(f"  PASS  {method:6} {path}  -> {code}")
    else:
        failed += 1
        print(f"  FAIL  {method:6} {path}  -> {code} (expected {expect})")
        print(f"        {json.dumps(payload)[:300]}")
    return payload


def login(phone, password):
    r = call("POST", "/api/auth/login", {"phone": phone, "password": password})
    return r["data"]["token"], r["data"]["user"]["id"]


print("=" * 62)
print("ServeNow API end-to-end test")
print("=" * 62)

print("\n[1] Health & root")
call("GET", "/health")
call("GET", "/")

print("\n[2] Authentication")
cust_token, cust_id = login("9876543211", "customer123")
prov_token, prov_id = login("9123456781", "provider123")
admin_token, admin_id = login("9999999999", "admin123")
call("GET", "/api/auth/me", token=cust_token)
call("POST", "/api/auth/login", {"phone": "9876543211", "password": "wrong"}, expect=401)
call("POST", "/api/auth/send-otp?phone=9876543211")

print("\n[3] Services (public)")
services = call("GET", "/api/services/")
call("GET", "/api/services/categories")
svc_id = services["data"][0]["_id"]
call("GET", f"/api/services/{svc_id}")

print("\n[4] Provider search")
call("GET", "/api/providers/search?lat=19.076&lng=72.877&radius=25")

print("\n[5] Booking lifecycle")
booking = call("POST", "/api/bookings/", {
    "provider_id": prov_id,
    "service_id": svc_id,
    "service_date": "2026-11-01T10:00:00",
    "service_time": "10:00 AM",
    "address": "101 Test Road, Bandra",
    "city": "Mumbai",
    "issue_description": "Fan not working",
    "payment_method": "upi"
}, token=cust_token)
booking_id = booking["data"]["booking_id"]
print(f"        booking={booking_id} ref={booking['data']['booking_ref']} "
      f"total={booking['data']['pricing']['total_amount']}")

call("GET", f"/api/bookings/{booking_id}", token=cust_token)
call("GET", "/api/bookings/", token=cust_token)
call("GET", "/api/bookings/", token=prov_token)

print("\n[6] Provider actions (confirm -> start -> complete)")
call("PUT", f"/api/bookings/{booking_id}/confirm", token=prov_token)
call("PUT", f"/api/bookings/{booking_id}/start", token=prov_token)
call("PUT", f"/api/bookings/{booking_id}/location?lat=19.0760&lng=72.8777", token=prov_token)
call("PUT", f"/api/bookings/{booking_id}/complete", token=prov_token)
call("PUT", f"/api/bookings/{booking_id}/cancel", token=cust_token, expect=400)

print("\n[7] Payments (demo mode)")
order = call("POST", f"/api/payments/create-order?booking_id={booking_id}", token=cust_token)
call("POST", f"/api/payments/verify?booking_id={booking_id}"
             f"&razorpay_order_id={order['data']['order_id']}"
             f"&razorpay_payment_id=demo_pay_1&razorpay_signature=demo", token=cust_token)
call("GET", f"/api/payments/status/{booking_id}", token=cust_token)

print("\n[8] Reviews")
call("POST", "/api/reviews/", {"booking_id": booking_id, "rating": 5,
                               "review": "Excellent work, fast and clean."}, token=cust_token)
call("POST", "/api/reviews/", {"booking_id": booking_id, "rating": 4}, token=cust_token, expect=400)
call("GET", f"/api/reviews/provider/{prov_id}")

print("\n[9] Notifications")
notifs = call("GET", "/api/notifications/", token=cust_token)
if notifs["data"]:
    call("PUT", f"/api/notifications/{notifs['data'][0]['_id']}/read", token=cust_token)
call("PUT", "/api/notifications/read-all", token=cust_token)

print("\n[10] Wallet & addresses")
call("GET", "/api/users/wallet", token=cust_token)
call("GET", "/api/users/addresses", token=cust_token)
call("POST", "/api/users/addresses", {
    "type": "work", "label": "Office", "address": "22 Business Park",
    "city": "Mumbai", "state": "Maharashtra", "pincode": "400001"
}, token=cust_token)

print("\n[11] Provider profile & earnings")
call("GET", "/api/providers/profile", token=prov_token)
call("PUT", "/api/providers/toggle-online", token=prov_token)
call("GET", "/api/providers/earnings", token=prov_token)

print("\n[12] Admin")
dash = call("GET", "/api/admin/dashboard", token=admin_token)
print(f"        users={dash['data']['users']['total']} "
      f"providers={dash['data']['providers']['total']} "
      f"bookings={dash['data']['bookings']['total']} "
      f"revenue={dash['data']['revenue']['total']}")
call("GET", "/api/admin/providers/pending", token=admin_token)
call("GET", "/api/admin/bookings", token=admin_token)
call("GET", "/api/admin/revenue?days=30", token=admin_token)

print("\n[13] Role enforcement")
call("GET", "/api/admin/dashboard", token=cust_token, expect=403)
call("GET", "/api/providers/profile", token=cust_token, expect=403)

print("\n" + "=" * 62)
print(f"RESULT: {passed} passed, {failed} failed")
print("=" * 62)
raise SystemExit(1 if failed else 0)
