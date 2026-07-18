from datetime import date
from datetime import datetime
from zoneinfo import ZoneInfo


def utcnow() -> datetime:
    return datetime.now(ZoneInfo("UTC"))


def entity_code(prefix: str, entity_id: int) -> str:
    """Return the human-readable operational identifier for an entity."""
    return f"{prefix}-{entity_id:06d}"


__all__ = ["utcnow", "date", "entity_code"]