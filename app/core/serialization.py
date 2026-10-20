from bson import ObjectId
from datetime import date, datetime
from decimal import Decimal


def to_jsonable(value):
    """Convert MongoDB-native types into JSON-safe Python values.

    MongoDB returns ObjectId for ``_id`` and datetime objects for timestamps.
    FastAPI cannot serialize either inside a plain ``dict`` response, so every
    document returned by a route has to pass through here first.
    """
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, set):
        return [to_jsonable(v) for v in value]
    return value
