"""API error handling."""

from enum import Enum
import json
from datetime import datetime


class ErrorCode(Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    SERVER_ERROR = "SERVER_ERROR"
    UNAVAILABLE = "UNAVAILABLE"


class APIError(Exception):
    def __init__(self, code, message, status=400):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)

    def to_dict(self):
        return {"success": False, "error": {"code": self.code.value, "message": self.message}}


def handle_error(error):
    if isinstance(error, APIError):
        return json.dumps(error.to_dict()), error.status
    else:
        return json.dumps(
            {"success": False, "error": {"code": "SERVER_ERROR", "message": str(error)}}
        ), 500


def success_response(data):
    return {"success": True, "data": data, "timestamp": datetime.utcnow().isoformat() + "Z"}


def validate_domain(domain):
    if not domain:
        raise APIError("INVALID_REQUEST", "Domain is required", 400)
    domain = domain.strip().lower()
    if len(domain) > 253:
        raise APIError("INVALID_REQUEST", "Domain too long", 400)
    return domain


def validate_limit(limit, default=100, max_limit=1000):
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        return default
    return min(max(limit, 1), max_limit)
