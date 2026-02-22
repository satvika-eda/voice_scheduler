from datetime import datetime, timezone
from dateutil import parser

def parse_datetime(datetime_str: str) -> datetime:
    try:
        dt = parser.isoparse(datetime_str)
    except Exception:
        dt = parser.parse(datetime_str, fuzzy=True)

    # make timezone-aware (UTC) if naive
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt