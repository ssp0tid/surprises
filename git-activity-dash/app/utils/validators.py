"""Input validation utilities."""

import os
import re
from urllib.parse import unquote

from git.exc import GitError


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def validate_repo_path(path: str) -> str:
    """Validate and sanitize repository path.

    Args:
        path: URL-encoded or raw repository path

    Returns:
        Sanitized absolute path

    Raises:
        ValidationError: If path is invalid or contains traversal attempts
    """
    if not path:
        raise ValidationError("Path is required", "PATH_REQUIRED", 400)

    decoded_path = unquote(path)

    if ".." in decoded_path or decoded_path.startswith("/"):
        resolved = os.path.abspath(decoded_path)
    else:
        resolved = os.path.abspath(os.path.join(os.getcwd(), decoded_path))

    if not os.path.exists(resolved):
        raise ValidationError(
            f"Repository path does not exist", "REPO_NOT_FOUND", 404, resolved
        )

    return resolved


def validate_git_repository(path: str) -> bool:
    """Validate that path is a valid git repository.

    Args:
        path: Absolute path to repository

    Returns:
        True if valid git repository

    Raises:
        ValidationError: If not a valid git repository
    """
    git_dir = os.path.join(path, ".git")

    if not os.path.isdir(git_dir):
        raise ValidationError(
            "Not a valid git repository (no .git directory)", "NOT_GIT_REPO", 422, path
        )

    return True


def validate_pagination(page: int, per_page: int, max_per_page: int) -> tuple:
    """Validate pagination parameters.

    Args:
        page: Page number (1-indexed)
        per_page: Items per page
        max_per_page: Maximum allowed items per page

    Returns:
        Tuple of (page, per_page)

    Raises:
        ValidationError: If parameters are invalid
    """
    try:
        page = int(page)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = int(per_page)
        if per_page < 1:
            per_page = 50
        elif per_page > max_per_page:
            per_page = max_per_page
    except (ValueError, TypeError):
        per_page = 50

    return page, per_page


def validate_date_range(start_date: str = None, end_date: str = None) -> tuple:
    """Validate and parse date range parameters.

    Args:
        start_date: Start date string (ISO format)
        end_date: End date string (ISO format)

    Returns:
        Tuple of (start_date, end_date) as datetime objects

    Raises:
        ValidationError: If dates are invalid
    """
    from datetime import datetime

    parsed_start = None
    parsed_end = None

    if start_date:
        try:
            parsed_start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            raise ValidationError("Invalid start date format", "INVALID_DATE", 400)

    if end_date:
        try:
            parsed_end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            raise ValidationError("Invalid end date format", "INVALID_DATE", 400)

    if parsed_start and parsed_end and parsed_start > parsed_end:
        raise ValidationError(
            "Start date must be before end date", "INVALID_DATE_RANGE", 400
        )

    return parsed_start, parsed_end
