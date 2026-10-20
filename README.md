# ServeNow Backend API

Complete Python/FastAPI backend for the ServeNow local services marketplace.

## Features

- **Authentication**: JWT-based auth with OTP verification
- **Role-based Access**: Customer, Provider, Admin roles
- **Service Management**: CRUD operations for services
- **Booking System**: Full booking lifecycle with status tracking
- **Payment Integration**: Razorpay payment gateway with 10% platform commission
- **Real-time Features**: WebSocket for live tracking and chat
- **Geospatial Search**: Location-based provider search
- **Review System**: Customer ratings and reviews
- **Admin Dashboard**: Revenue tracking, provider approvals, analytics
- **Notifications**: Push notifications for booking updates

## Tech Stack

- **Framework**: FastAPI
- **Database**: MongoDB (async with motor) — MongoDB Atlas or local
- **Authentication**: JWT tokens with bcrypt
- **Payments**: Razorpay
- **Real-time**: WebSockets
- **Validation**: Pydantic v2

## Project Structure

```
servenow-backend-python/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Python dependencies
├── seed.py                 # Database seeder
├── e2e_test.py             # REST end-to-end test
├── ws_test.py              # WebSocket end-to-end test
├── .env.example            # Environment variables template
└── app/
    ├── core/
    │   ├── config.py         # App configuration
    │   ├── database.py       # MongoDB connection + ObjectId helpers
    │   ├── security.py       # JWT, password hashing, pricing calculation
    │   ├── serialization.py  # MongoDB -> JSON conversion
    │   ├── time_utils.py     # Naive-UTC timestamp helper
    │   └── dependencies.py   # Auth dependencies
    ├── models/
    │   └── schemas.py        # Pydantic models
    ├── api/
    │   └── routes/
    │       ├── auth.py        # Authentication endpoints
    │       ├── users.py       # User management
    │       ├── providers.py   # Provider endpoints
    │       ├── services.py    # Service CRUD
    │       ├── bookings.py    # Booking lifecycle
    │       ├── payments.py    # Payment processing
    │       ├── reviews.py     # Reviews & ratings
    │       ├── admin.py       # Admin dashboard
    │       └── notifications.py # Notifications
    └── websocket/
        └── handler.py        # WebSocket handler
```

## Setup Instructions

### Prerequisites

- Python 3.9+ (tested on 3.13)
- A MongoDB instance — [MongoDB Atlas](https://cloud.mongodb.com) (free tier) or local

### Installation

1. **Create the virtual environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS/Linux
   ```

2. **Install dependencies**:
   ```bash
   .venv\Scripts\pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env          # Windows: copy .env.example .env
   ```
   Edit `.env` and set at minimum:
   ```env
   MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net
   DATABASE_NAME=servenow
   SECRET_KEY=<a-long-random-string>
   ```

4. **Seed the database** (optional):
   ```bash
   .venv\Scripts\python seed.py
   ```

5. **Run the server**:
   ```bash
   .venv\Scripts\python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API is available at `http://localhost:8000`
   API documentation at `http://localhost:8000/docs`

## Testing

Both test scripts run against a live server on port 8000:

```bash
.venv\Scripts\python e2e_test.py   # 42 REST checks
.venv\Scripts\python ws_test.py    # 7 WebSocket checks
```

### Seeded test credentials
- **Admin**: phone=9999999999, password=admin123
- **Customer**: phone=9876543211, password=customer123
- **Provider**: phone=9123456781, password=provider123

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/send-otp` - Send OTP
- `POST /api/auth/verify-otp` - Verify OTP
- `GET /api/auth/me` - Get current user
- `PUT /api/auth/profile` - Update profile

### Users
- `GET /api/users/addresses` - Get addresses
- `POST /api/users/addresses` - Add address
- `GET /api/users/wallet` - Get wallet
- `PUT /api/users/fcm-token` - Update FCM token

### Providers
- `POST /api/providers/register` - Register as provider
- `GET /api/providers/profile` - Get provider profile
- `PUT /api/providers/profile` - Update profile
- `PUT /api/providers/toggle-online` - Toggle online status
- `GET /api/providers/earnings` - Get earnings
- `GET /api/providers/search` - Search providers by location
- `GET /api/providers/{id}` - Get provider by ID

### Services
- `POST /api/services/` - Create service (admin)
- `GET /api/services/` - Get all services
- `GET /api/services/categories` - Get categories
- `GET /api/services/{id}` - Get service by ID
- `PUT /api/services/{id}` - Update service (admin)
- `DELETE /api/services/{id}` - Delete service (admin)

### Bookings
- `POST /api/bookings/` - Create booking
- `GET /api/bookings/` - Get user bookings
- `GET /api/bookings/{id}` - Get booking details
- `PUT /api/bookings/{id}/confirm` - Confirm booking (provider)
- `PUT /api/bookings/{id}/start` - Start service (provider)
- `PUT /api/bookings/{id}/complete` - Complete service (provider)
- `PUT /api/bookings/{id}/cancel` - Cancel booking
- `PUT /api/bookings/{id}/location` - Update location (provider)

### Payments
- `POST /api/payments/create-order` - Create payment order
- `POST /api/payments/verify` - Verify payment
- `GET /api/payments/status/{booking_id}` - Get payment status
- `POST /api/payments/refund/{booking_id}` - Refund payment

### Reviews
- `POST /api/reviews/` - Create review
- `GET /api/reviews/provider/{id}` - Get provider reviews

### Admin
- `GET /api/admin/dashboard` - Get dashboard stats
- `GET /api/admin/providers/pending` - Get pending providers
- `PUT /api/admin/providers/{id}/approve` - Approve provider
- `PUT /api/admin/providers/{id}/reject` - Reject provider
- `GET /api/admin/bookings` - Get all bookings
- `GET /api/admin/revenue` - Get revenue report

### Notifications
- `GET /api/notifications/` - Get notifications
- `PUT /api/notifications/{id}/read` - Mark as read
- `PUT /api/notifications/read-all` - Mark all as read

### WebSocket
- `ws://localhost:8000/ws?token=<jwt_token>` - Real-time updates
  - Location tracking (`location_update`)
  - Chat messages (`chat_message`)
  - Booking status updates (`booking_status`)
  - Keep-alive (`ping` / `pong`)

## ID Conventions

Two kinds of identifiers are in play, and mixing them was the source of most
of the bugs in the original code:

| Field | Value | Where it comes from |
|---|---|---|
| `users._id` | ObjectId | MongoDB |
| `providers._id` | ObjectId | MongoDB |
| `providers.user_id` | string | the user's ObjectId as a string |
| `bookings.customer_id` | string | the user's ObjectId as a string |
| `bookings.provider_id` | string | the **provider document's** ObjectId as a string |

IDs arrive over HTTP as strings but MongoDB stores them as ObjectIds, so every
lookup converts first. `app/core/database.py` exposes two helpers:

- `to_object_id(value)` — convert a string id to an ObjectId when it is one
- `app/core/serialization.py:to_jsonable(value)` — convert ObjectId and
  datetime values in a document into JSON-safe values

Provider-scoped routes resolve the provider document from the authenticated
user id (see `provider_doc_id` in `app/api/routes/bookings.py`), so a provider
only ever needs their own user id.

## Timestamps

The MongoDB client is not timezone aware, so all timestamps are stored and
compared as **naive UTC**. `datetime.utcnow()` is deprecated from Python 3.12
onwards, so `app/core/time_utils.py` provides `utcnow()`, which returns the
current UTC time as a naive datetime and preserves that exact behaviour.

## Business Model

**Platform Commission**: 10% on every booking

**Pricing Calculation**:
- Service charge: Rs. 500 (example)
- Platform fee (10%): Rs. 50
- GST on platform fee (18%): Rs. 9
- **Total customer pays**: Rs. 509
- **Provider earns**: Rs. 450

## Production Deployment

1. Update `.env` with production values (Atlas cluster, real Razorpay keys)
2. Set `DEBUG=False`
3. Use a production server:
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```
4. Configure Razorpay production keys (the API falls back to demo mode when they are blank)
5. Set up Firebase for push notifications
6. Use a reverse proxy (nginx) and SSL

## License

Proprietary - ServeNow Platform
