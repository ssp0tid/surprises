"""Date and time utilities."""

from datetime import datetime, timezone


def format_timestamp(timestamp: int, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format Unix timestamp to string."""
    if timestamp == 0:
        return "unknown"
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime(fmt)


def format_relative_time(timestamp: int) -> str:
    """Format timestamp as relative time (e.g., '2 hours ago')."""
    if timestamp == 0:
        return "unknown"

    now = datetime.now(timezone.utc)
    then = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    diff = now - then

    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    if seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    if seconds < 604800:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    if seconds < 2592000:
        weeks = int(seconds // 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    if seconds < 31536000:
        months = int(seconds // 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"

    years = int(seconds // 31536000)
    return f"{years} year{'s' if years != 1 else ''} ago"


def parse_date(date_str: str) -> int | None:
    """Parse date string to Unix timestamp."""
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m",
        "%Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return int(dt.timestamp())
        except ValueError:
            continue

    return None


def format_short_date(timestamp: int) -> str:
    """Format timestamp as short date."""
    if timestamp == 0:
        return "----"
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d")
