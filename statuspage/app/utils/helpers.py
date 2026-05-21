import json
from datetime import datetime, timedelta

from markupsafe import Markup


def format_datetime(value, format="%Y-%m-%d %H:%M:%S"):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return value
    return value.strftime(format)


def format_relative_time(value):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return value

    now = datetime.utcnow()
    diff = now - value

    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=30):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return value.strftime("%Y-%m-%d")


def status_badge(status):
    colors = {
        "operational": "#22c55e",
        "degraded": "#f59e0b",
        "down": "#ef4444",
        "unknown": "#6b7280",
        "investigating": "#f59e0b",
        "identified": "#f59e0b",
        "monitoring": "#3b82f6",
        "resolved": "#22c55e",
    }
    color = colors.get(status, "#6b7280")

    return Markup(
        f'<span class="status-badge" style="background:{color}">{status}</span>'
    )


def calculate_uptime_percentage(results):
    if not results:
        return 100.0

    total = len(results)
    operational = sum(1 for r in results if r.status == "operational")
    return round((operational / total) * 100, 2)


def generate_chart_data(history, buckets=24):
    if not history:
        return {"labels": [], "data": []}

    bucket_size = len(history) // buckets
    if bucket_size == 0:
        return {"labels": [], "data": []}

    data = []
    labels = []

    for i in range(0, len(history), bucket_size):
        bucket = history[i : i + bucket_size]
        pct = calculate_uptime_percentage(bucket)
        data.append(pct)

        if bucket:
            first = bucket[0].checked_at
            labels.append(first.strftime("%H:00"))

    return {"labels": labels, "data": data}


def sanitized_json(value):
    if value is None:
        return "{}"
    if isinstance(value, str):
        try:
            json.loads(value)
            return value
        except (json.JSONDecodeError, TypeError):
            return "{}"
    return json.dumps(value)
