from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from bson.errors import InvalidId
from app.core.config import settings
import sys

# Windows consoles default to cp1252 and cannot encode the status symbols used
# in the startup logs. Fall back to UTF-8 with replacement instead of crashing.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

client: AsyncIOMotorClient = None
db = None

async def connect_db():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]

    # Create indexes
    await db.users.create_index("phone", unique=True)
    await db.users.create_index("email", sparse=True)
    await db.providers.create_index([("location", "2dsphere")])
    await db.bookings.create_index([("customer_id", 1), ("status", 1)])
    await db.bookings.create_index([("provider_id", 1), ("status", 1)])

    print("✅ Connected to MongoDB")

async def disconnect_db():
    global client
    if client:
        client.close()
        print("✅ Disconnected from MongoDB")

def get_database():
    return db

def to_object_id(value):
    """Convert a string id to an ObjectId when it looks like one.

    IDs travel through the API as strings, but MongoDB stores them as ObjectIds.
    Querying with a raw string never matches, so every lookup has to convert.
    Values that are not valid ObjectIds are returned unchanged.
    """
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return value
