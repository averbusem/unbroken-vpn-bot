from datetime import datetime
from zoneinfo import ZoneInfo

TIMEZONE: str = "Europe/Moscow"


def format_utc_to_moscow(dt: datetime, fmt: str = "%d.%m.%Y %H:%M") -> str:
    return dt.astimezone(ZoneInfo(TIMEZONE)).strftime(fmt) + " MSK"


def format_days_string(n: int) -> str:
    """
    Правильно обрабатывает падежи: день, дня, дней
    """
    if n % 10 == 1 and n % 100 != 11:
        form = "день"
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        form = "дня"
    else:
        form = "дней"
    return f"{n} {form}"
