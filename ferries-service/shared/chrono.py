
from datetime import datetime, timezone

def utc_now() -> datetime:
    """Get the current UTC time."""
    return datetime.now(timezone.utc).replace(tzinfo=None)