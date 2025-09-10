from datetime import datetime, timezone
from collections.abc import Sequence


def make_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def normalize_dates(data: dict, fields: Sequence[str]) -> dict:
    """
    Makes dates timezone-aware for the specified fields.
    """
    for field in fields:
        if field in data and data[field]:
            data[field] = make_aware(data[field])
    return data


