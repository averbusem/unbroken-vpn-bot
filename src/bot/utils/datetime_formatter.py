from datetime import datetime
from zoneinfo import ZoneInfo

TIMEZONE: str = "Europe/Moscow"


def format_utc_to_moscow(dt: datetime, fmt: str = "%d.%m.%Y %H:%M") -> str:
    return dt.astimezone(ZoneInfo(TIMEZONE)).strftime(fmt) + " MSK"
