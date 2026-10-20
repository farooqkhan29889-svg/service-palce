from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current UTC time as a naive datetime.

    ``datetime.utcnow()`` is deprecated from Python 3.12 onwards. The MongoDB
    client is not timezone aware, so timestamps are stored and compared as
    naive UTC values - this keeps that exact behaviour without the warning.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
