from datetime import datetime


def format_datetime(dt):
    """Format datetime to ISO 8601 string"""
    if dt is None:
        return None
    return dt.isoformat() + "Z"


def parse_bool(value):
    """Parse boolean from various representations"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)
