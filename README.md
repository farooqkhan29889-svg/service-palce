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

## Deployment

### Render (one-click blueprint)

`render.yaml` in the repo root defines the whole service, so Render can build
and deploy it without any manual configuration beyond the secrets.

1. Push the code to GitHub (done - the repo is the deployment source).
2. Open the Render dashboard and choose **New -> Blueprint**.
3. Connect the repository `farooqkhan29889-svg/service-palce`.
4. Render reads `render.yaml` and asks for the values marked `sync: false`:
   - `MONGODB_URI` - the MongoDB Atlas connection string
   - `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` - leave blank for demo mode
   - `REDIS_URL` - optional, only needed once WebSockets scale past one worker
5. `SECRET_KEY` is generated automatically by Render.
6. Click **Apply**. The first build takes 2-4 minutes.

Once deployed the service is reachable at:

```
https://servenow-api.onrender.com
https://servenow-api.onrender.com/docs
https://servenow-api.onrender.com/health
wss://servenow-api.onrender.com/ws?token=<jwt>
```

### MongoDB Atlas access list

Render's outbound IP addresses are not fixed, so the Atlas project must allow
them. In the Atlas UI go to **Network Access -> Access List** and add:

```
0.0.0.0/0    (Allow access from anywhere)
```

Without this entry the container cannot open the database connection and the
service will fail its health check. Replace it with Render's published static
IP ranges once you move to a paid plan.

### Environment variables

| Variable | Required | Notes |
|---|---|---|
| `MONGODB_URI` | yes | `mongodb+srv://user:password@cluster.mongodb.net` |
| `SECRET_KEY` | yes | Render generates one; rotate it if it ever leaks |
| `DATABASE_NAME` | yes | `servenow` |
| `DEBUG` | yes | Set to `false` in production |
| `CORS_ORIGINS` | yes | JSON list of allowed frontend origins |
| `ALGORITHM` | no | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | `10080` (7 days) |
| `PLATFORM_COMMISSION_RATE` | no | `0.10` |
| `GST_RATE` | no | `0.18` |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | no | Blank switches payments to demo mode |
| `REDIS_URL` | no | Reserved for cross-worker WebSocket fan-out |

### Connecting the frontend

- REST base URL: `https://servenow-api.onrender.com`
- WebSocket URL: `wss://servenow-api.onrender.com/ws?token=<jwt>`
- Add the frontend origin to `CORS_ORIGINS`, otherwise the browser blocks
  every call.

### Scaling notes

The WebSocket connection registry lives in process memory
(`app/websocket/handler.py`), so the service deliberately runs with
**one worker**. A second gunicorn worker would not see connections opened on
the first, and live location and chat updates would be silently dropped.

To scale out, move the broadcast fan-out to Redis pub/sub (the `REDIS_URL`
variable is already reserved for that) and then raise `--workers`.

### Free tier caveats

Render's free plan spins the service down after 15 minutes of inactivity and
restarts it on the next request, which drops any open WebSocket. The client
must reconnect on close. Move to the `starter` plan for a production API with
live tracking.

### Other platforms

`Procfile` is included and works on Railway, Heroku and any other platform
that reads it:

```
web: gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

For Docker or a plain VPS, build with `pip install -r requirements.txt` and run
that command behind nginx with TLS termination.

## License

Proprietary - ServeNow Platform
