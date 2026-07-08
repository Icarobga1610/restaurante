from datetime import date
from datetime import datetime
from zoneinfo import ZoneInfo


def utcnow() -> datetime:
    return datetime.now(ZoneInfo("UTC"))


__all__ = ["utcnow", "date"]