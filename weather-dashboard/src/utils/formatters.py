"""Data formatting utilities."""

from datetime import datetime, date
from typing import Optional


def format_time(dt: datetime) -> str:
    """Format datetime to time string (HH:MM)."""
    return dt.strftime("%H:%M")


def format_date(d: date) -> str:
    """Format date to string (YYYY-MM-DD)."""
    return d.strftime("%Y-%m-%d")


def format_day_name(d: date, short: bool = True) -> str:
    """Format date to day name."""
    if short:
        return d.strftime("%a")  # Mon, Tue, etc.
    return d.strftime("%A")  # Monday, Tuesday, etc.


def format_datetime(dt: datetime) -> str:
    """Format datetime to full string."""
    return dt.strftime("%Y-%m-%d %H:%M")


def format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time (e.g., '2 hours ago')."""
    now = datetime.now()
    diff = now - dt
    
    if diff.total_seconds() < 60:
        return "just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} min{' ago" if minutes > 1 else " ago"}"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        days = int(diff.total_seconds() / 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"


def format_percentage(value: float, decimals: int = 0) -> str:
    """Format float as percentage."""
    return f"{value:.{decimals}f}%"


def format_precipitation(value: float, unit: str = "mm") -> str:
    """Format precipitation value."""
    if value == 0:
        return "0"
    elif value < 1:
        return f"{value:.1f}"
    else:
        return f"{value:.0f}"


def format_cloud_cover(cloud_cover: int) -> str:
    """Format cloud cover as descriptive text."""
    if cloud_cover < 10:
        return "Clear"
    elif cloud_cover < 25:
        return "Mostly Clear"
    elif cloud_cover < 50:
        return "Partly Cloudy"
    elif cloud_cover < 75:
        return "Mostly Cloudy"
    else:
        return "Overcast"


def format_humidity(humidity: int) -> str:
    """Format humidity with descriptive text."""
    if humidity < 30:
        return f"{humidity}% (Dry)"
    elif humidity < 60:
        return f"{humidity}% (Comfortable)"
    elif humidity < 80:
        return f"{humidity}% (Humid)"
    else:
        return f"{humidity}% (Very Humid)"


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def center_text(text: str, width: int, fill_char: str = " ") -> str:
    """Center text within a given width."""
    padding = max(0, width - len(text)) // 2
    return fill_char * padding + text + fill_char * (width - len(text) - padding)


def right_align(text: str, width: int, fill_char: str = " ") -> str:
    """Right-align text within a given width."""
    padding = max(0, width - len(text))
    return fill_char * padding + text


def left_align(text: str, width: int, fill_char: str = " ") -> str:
    """Left-align text within a given width."""
    padding = max(0, width - len(text))
    return text + fill_char * padding


def create_box_line(content: str, width: int, padding: int = 1) -> str:
    """Create a box line with content centered or left-aligned."""
    inner_width = width - 2 - (padding * 2)  # -2 for borders, -padding*2 for internal padding
    padded_content = content[:inner_width].center(inner_width)
    return f"│{' ' * padding}{padded_content}{' ' * padding}│"


def create_box_top(width: int) -> str:
    """Create top border of a box."""
    return "┌" + "─" * (width - 2) + "┐"


def create_box_bottom(width: int) -> str:
    """Create bottom border of a box."""
    return "└" + "─" * (width - 2) + "┘"


def create_box_divider(width: int) -> str:
    """Create divider line for a box."""
    return "├" + "─" * (width - 2) + "┤"
