"""Cron expression parser, validator, and next-run calculator."""

from datetime import datetime, timedelta
from typing import Optional

try:
    import croniter

    HAS_CRONITER = True
except ImportError:
    HAS_CRONITER = False


MONTH_MAP = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

WEEKDAY_MAP = {
    "sun": 0,
    "mon": 1,
    "tue": 2,
    "wed": 3,
    "thu": 4,
    "fri": 5,
    "sat": 6,
}


class CronParseError(Exception):
    pass


def validate(expression: str) -> tuple[bool, Optional[str]]:
    if not HAS_CRONITER:
        return _simple_validate(expression)
    try:
        croniter(expression)
        return True, None
    except (KeyError, ValueError) as e:
        return False, str(e)
    except Exception as e:
        return False, f"Invalid expression: {str(e)}"


def _simple_validate(expression: str) -> tuple[bool, Optional[str]]:
    parts = expression.strip().split()
    if len(parts) != 5:
        return False, f"Expected 5 fields, got {len(parts)}"
    for i, field in enumerate(parts):
        if _validate_field(field, i) is None:
            return False, f"Invalid field {i + 1}: {field}"
    return True, None


def _validate_field(field: str, index: int) -> Optional[set]:
    ranges = [
        (0, 59),
        (0, 23),
        (1, 31),
        (1, 12),
        (0, 6),
    ][index]
    min_val, max_val = ranges

    if field == "*":
        return set(range(min_val, max_val + 1))

    valid_vals = set()
    for part in field.split(","):
        if "/" in part:
            base, step = part.split("/")
            if base == "*":
                start, stop = min_val, max_val
            elif "-" in base:
                start, stop = map(int, base.split("-"))
            else:
                start = int(base)
                stop = max_val
            step = int(step)
            for v in range(start, stop + 1, step):
                if min_val <= v <= max_val:
                    valid_vals.add(v)
        elif "-" in part:
            start, stop = map(int, part.split("-"))
            for v in range(start, stop + 1):
                if min_val <= v <= max_val:
                    valid_vals.add(v)
        else:
            try:
                v = int(part.strip())
                if min_val <= v <= max_val:
                    valid_vals.add(v)
            except ValueError:
                pass

    return valid_vals if valid_vals else None


def get_next_run(expression: str, count: int = 5) -> list[datetime]:
    if not HAS_CRONITER:
        return _simple_get_next_run(expression, count)

    try:
        base = datetime.now()
        cron = croniter(expression, base)
        runs = []
        for _ in range(count):
            next_time = cron.get_next(datetime)
            runs.append(next_time.replace(second=0, microsecond=0))
        return runs
    except Exception:
        return []


def _simple_get_next_run(expression: str, count: int) -> list[datetime]:
    parts = expression.strip().split()
    if len(parts) != 5:
        return []

    fields = [_validate_field(f, i) for i, f in enumerate(parts)]
    if any(f is None for f in fields):
        return []

    runs = []
    current = datetime.now().replace(second=0, microsecond=0)
    checked = 0
    max_iterations = 525600

    while len(runs) < count and checked < max_iterations:
        checked += 1
        current += timedelta(minutes=1)

        if (
            current.minute in fields[0]
            and current.hour in fields[1]
            and current.day in fields[2]
            and current.month in fields[3]
            and current.weekday() in fields[4]
        ):
            runs.append(current.replace(second=0, microsecond=0))

    return runs


def to_human_readable(expression: str) -> str:
    if not HAS_CRONITER:
        return _simple_to_human(expression)

    try:
        return _croniter_desc(expression)
    except Exception:
        return "Invalid expression"


def _croniter_desc(expression: str) -> str:
    parts = expression.strip().split()
    if len(parts) != 5:
        return "Invalid expression"

    minute, hour, day, month, weekday = parts

    desc = []

    if minute == "*" and hour == "*" and day == "*" and month == "*" and weekday == "*":
        return "Every minute"

    if minute != "*":
        if "/" in minute:
            step = minute.split("/")[1]
            desc.append(f"every {step} minutes")
        elif minute == "0":
            desc.append("at minute 0")
        else:
            desc.append(f"minute {minute}")

    if hour != "*":
        if "/" in hour:
            step = hour.split("/")[1]
            desc.append(f"every {step} hours")
        elif hour == "0":
            desc.append(f"at {hour}:00")
        else:
            desc.append(f"hour {hour}")

    if day != "*" and day != "?":
        desc.append(f"day {day}")

    if month != "*" and month != "?":
        month_names = [
            "",
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        try:
            m = int(month)
            if 1 <= m <= 12:
                desc.append(month_names[m])
        except (ValueError, IndexError):
            desc.append(f"month {month}")

    if weekday != "*" and weekday != "?":
        weekday_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        try:
            wd = int(weekday)
            if 0 <= wd <= 6:
                desc.append(weekday_names[wd])
        except (ValueError, IndexError):
            desc.append(f"weekday {weekday}")

    if not desc:
        return expression
    return " ".join(desc)


def _simple_to_human(expression: str) -> str:
    parts = expression.strip().split()
    if len(parts) != 5:
        return "Invalid expression (need 5 fields)"

    minute, hour, day, month, weekday = parts

    if minute == "*" and hour == "*" and day == "*" and month == "*" and weekday == "*":
        return "Every minute"

    if minute == "0" and hour != "*":
        return f"Daily at {hour}:00"

    if weekday not in ["*", "?"]:
        weekday_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        if weekday in ["1-5", "1,2,3,4,5"]:
            return f"Weekdays at {hour}:00"
        try:
            wd = int(weekday.split(",")[0])
            return f"Every {weekday_names[wd]} at {hour}:00"
        except (ValueError, IndexError):
            pass

    return f"Schedule: {expression}"
