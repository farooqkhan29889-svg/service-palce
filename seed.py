"""
Database seeder for ServeNow
Run this to populate the database with sample data for testing
"""
import asyncio
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.core.database import connect_db, get_database
from app.core.security import get_password_hash
from app.core.time_utils import utcnow

async def seed_database():
    """Seed the database with sample data"""
    await connect_db()
    db = get_database()

    print("🌱 Seeding database...")

    # Clear existing data
    await db.users.delete_many({})
    await db.providers.delete_many({})
    await db.services.delete_many({})
    await db.bookings.delete_many({})
    await db.payments.delete_many({})
    await db.reviews.delete_many({})
    await db.notifications.delete_many({})
    await db.chat_messages.delete_many({})

    print("🗑️  Cleared existing data")

    # Create admin user
    admin_user = {
        "name": "Admin User",
        "phone": "9999999999",
        "email": "admin@servenow.com",
        "password": get_password_hash("admin123"),
        "role": "admin",
        "is_verified": True,
        "addresses": [],
        "wallet": {"balance": 0.0, "transactions": []},
        "created_at": utcnow(),
        "updated_at": utcnow()
    }
    await db.users.insert_one(admin_user)
    print("✅ Created admin user (phone: 9999999999, password: admin123)")

    # Create sample customers
    customers = []
    for i in range(1, 6):
        customer = {
            "name": f"Customer {i}",
            "phone": f"987654321{i}",
            "email": f"customer{i}@example.com",
            "password": get_password_hash("customer123"),
            "role": "customer",
            "is_verified": True,
            "addresses": [
                {
                    "type": "home",
                    "label": "Home",
                    "address": f"{i}00, Sample Street, Sector {i}",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "pincode": f"40000{i}",
                    "coordinates": {
                        "type": "Point",
                        "coordinates": [72.8777 + (i * 0.01), 19.0760 + (i * 0.01)]
                    },
                    "is_default": True,
                    "created_at": utcnow()
                }
            ],
            "wallet": {"balance": 500.0, "transactions": []},
            "created_at": utcnow(),
            "updated_at": utcnow()
        }
        result = await db.users.insert_one(customer)
        customers.append({"id": str(result.inserted_id), **customer})

    print(f"✅ Created {len(customers)} sample customers (password: customer123)")

    # Create services
    services = [
        {
            "name": "Electrician",
            "icon": "⚡",
            "description": "Electrical repairs, wiring, installations",
            "category": "Home Services",
            "base_price": 500,
            "duration": 60,
            "slug": "electrician",
            "is_active": True,
            "created_at": utcnow(),
            "updated_at": utcnow()
        },
        {
            "name": "Plumber",
            "icon": "🔧",
            "description": "Plumbing repairs, pipe fitting, water tank cleaning",
            "category": "Home Services",
            "base_price": 400,
            "duration": 45,
            "slug": "plumber",
            "is_active": True,
            "created_at": utcnow(),
            "updated_at": utcnow()
        },
        {
            "name": "Carpenter",
            "icon": "🪚",
            "description": "Furniture repair, woodwork, installations",
            "category": "Home Services",
            "base_price": 600,
            "duration": 90,
            "slug": "carpenter",
            "is_active": True,
            "created_at": utcnow(),
            "updated_at": utcnow()
        },
        {
            "name": "Painter",
            "icon": "🎨",
            "description": "Wall painting, texture work, waterproofing",
            "category": "Home Services",
            "base_price": 800,
            "duration": 120,
            "slug": "painter",
            "is_active": True,
            "created_at": utcnow(),
            "updated_at": utcnow()
        },
        {
            "name": "AC Repair",
            "icon": "❄️",
            "description": "AC installation, repair, gas refilling",
            "category": "Appliance Repair",
            "base_price": 700,
            "duration": 60,
            "slug": "ac-repair",
            "is_active": True,
            "created_at": utcnow(),
            "updated_at": utcnow()
        },
        {
            "name": "Labour",
            "icon": "👷",
            "description": "General labour, loading, unloading, shifting",
            "category": "Labour",
            "base_price": 300,
            "duration": 60,
            "slug": "labour",
            "is_active": True,
            "created_at": utcnow(),
            "updated_at": utcnow()
        }
    ]

    service_ids = []
    for service in services:
        result = await db.services.insert_one(service)
        service_ids.append(str(result.inserted_id))

    print(f"✅ Created {len(services)} services")

    # Create sample providers
    providers = []
    for i in range(1, 4):
        provider_user = {
            "name": f"Provider {i}",
            "phone": f"912345678{i}",
            "email": f"provider{i}@example.com",
            "password": get_password_hash("provider123"),
            "role": "provider",
            "is_verified": True,
            "addresses": [],
            "wallet": {"balance": 0.0, "transactions": []},
            "created_at": utcnow(),
            "updated_at": utcnow()
        }
        user_result = await db.users.insert_one(provider_user)
        user_id = str(user_result.inserted_id)

        provider = {
            "user_id": user_id,
            "services": service_ids[:2],  # First two services
            "experience_years": 3 + i,
            "aadhaar_number": f"12345678901{i}",
            "daily_wage": 500 + (i * 100),
            "skills": ["Experienced", "Reliable", "Skilled"],
            "is_approved": True,
            "is_online": i % 2 == 1,  # Alternate online status
            "rating": {"average": 4.0 + (i * 0.2), "count": 10 + i},
            "total_jobs": 20 + i,
            "completed_jobs": 18 + i,
            "cancelled_jobs": 2,
            "earnings": {"total": 15000 + (i * 5000), "this_month": 5000 + (i * 1000), "platform_fees_paid": 1500 + (i * 500)},
            "location": {
                "type": "Point",
                "coordinates": [72.8777 + (i * 0.02), 19.0760 + (i * 0.02)]
            },
            "created_at": utcnow(),
            "updated_at": utcnow()
        }
        provider_result = await db.providers.insert_one(provider)
        providers.append({"id": str(provider_result.inserted_id), "user_id": user_id, **provider})

    print(f"✅ Created {len(providers)} sample providers (password: provider123)")

    # Create sample bookings
    bookings = []
    for i in range(1, 4):
        customer = customers[i % len(customers)]
        provider = providers[i % len(providers)]
        service_id = service_ids[i % len(service_ids)]

        booking = {
            "booking_id": f"SN-TEST{i:06d}",
            "customer_id": customer["id"],
            "provider_id": provider["id"],
            "service_id": service_id,
            "service_name": services[i % len(services)]["name"],
            "service_date": utcnow(),
            "service_time": "10:00 AM",
            "address": f"{i}00, Test Street",
            "city": "Mumbai",
            "coordinates": {
                "type": "Point",
                "coordinates": [72.8777 + (i * 0.01), 19.0760 + (i * 0.01)]
            },
            "issue_description": f"Sample issue description {i}",
            "pricing": {
                "service_charge": 500,
                "platform_fee": 50,
                "platform_fee_percentage": 10,
                "gst": 9,
                "gst_percentage": 18,
                "total_amount": 509,
                "provider_earnings": 450
            },
            "payment": {
                "method": "upi",
                "status": "completed" if i < 3 else "pending",
                "amount": 509
            },
            "status": ["completed", "in_progress", "confirmed"][i % 3],
            "timeline": {
                "created_at": utcnow().isoformat(),
                "confirmed_at": utcnow().isoformat() if i != 2 else None,
                "started_at": utcnow().isoformat() if i == 1 else None,
                "completed_at": utcnow().isoformat() if i == 0 else None,
                "cancelled_at": None
            },
            "provider_location": None,
            "customer_rating": None,
            "created_at": utcnow(),
            "updated_at": utcnow()
        }
        result = await db.bookings.insert_one(booking)
        bookings.append(str(result.inserted_id))

    print(f"✅ Created {len(bookings)} sample bookings")

    print("\n🎉 Database seeding completed!")
    print("\n📋 Test Credentials:")
    print("   Admin:    phone=9999999999, password=admin123")
    print("   Customer: phone=9876543211, password=customer123")
    print("   Provider: phone=9123456781, password=provider123")

if __name__ == "__main__":
    asyncio.run(seed_database())
