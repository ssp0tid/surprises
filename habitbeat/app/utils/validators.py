"""Input validation utilities."""

import re
from datetime import datetime

from app.utils.errors import ValidationError


def validate_email(email):
    if not email:
        raise ValidationError(
            message="Email is required",
            details=[{"field": "email", "message": "Email is required"}],
        )
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise ValidationError(
            message="Invalid email format",
            details=[{"field": "email", "message": "Invalid email format"}],
        )
    return email


def validate_password(password, min_length=8):
    if not password:
        raise ValidationError(
            message="Password is required",
            details=[{"field": "password", "message": "Password is required"}],
        )
    if len(password) < min_length:
        raise ValidationError(
            message=f"Password must be at least {min_length} characters",
            details=[
                {
                    "field": "password",
                    "message": f"Password must be at least {min_length} characters",
                }
            ],
        )
    return password


def validate_habit_name(name):
    if not name or not name.strip():
        raise ValidationError(
            message="Habit name is required",
            details=[{"field": "name", "message": "Habit name is required"}],
        )
    if len(name) > 255:
        raise ValidationError(
            message="Habit name must be less than 255 characters",
            details=[{"field": "name", "message": "Habit name too long"}],
        )
    return name.strip()


def validate_frequency(frequency):
    valid_frequencies = ["daily", "weekly", "monthly"]
    if frequency not in valid_frequencies:
        raise ValidationError(
            message=f"Invalid frequency. Must be one of: {', '.join(valid_frequencies)}",
            details=[{"field": "frequency", "message": f"Invalid frequency"}],
        )
    return frequency


def validate_date_range(start_date, end_date):
    if start_date and end_date:
        start = datetime.fromisoformat(start_date.replace("Z", ""))
        end = datetime.fromisoformat(end_date.replace("Z", ""))
        if start > end:
            raise ValidationError(
                message="start_date must be before end_date",
                details=[{"field": "start_date", "message": "Invalid date range"}],
            )
    return True


def validate_category_name(name):
    if not name or not name.strip():
        raise ValidationError(
            message="Category name is required",
            details=[{"field": "name", "message": "Category name is required"}],
        )
    if len(name) > 100:
        raise ValidationError(
            message="Category name too long",
            details=[
                {
                    "field": "name",
                    "message": "Category name must be less than 100 characters",
                }
            ],
        )
    return name.strip()


def validate_hex_color(color):
    if color:
        hex_pattern = r"^#[0-9A-Fa-f]{6}$"
        if not re.match(hex_pattern, color):
            raise ValidationError(
                message="Invalid hex color format",
                details=[
                    {
                        "field": "color",
                        "message": "Must be valid hex color (e.g., #6366f1)",
                    }
                ],
            )
    return color
