"""Helper utility functions."""

import json
from urllib.parse import parse_qs, urlparse


def format_json(data, indent=2):
    """Format data as JSON string."""
    try:
        return json.dumps(data, indent=indent, sort_keys=False)
    except (TypeError, ValueError):
        return str(data)


def validate_json(data):
    """Validate JSON string or return parsed data."""
    if isinstance(data, dict):
        return data
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None


def parse_query_params(query_string):
    """Parse query string into dict."""
    if not query_string:
        return {}
    parsed = parse_qs(query_string, keep_blank_values=True)
    return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}


def extract_path_params(path_pattern, request_path):
    """Extract parameters from request path based on pattern."""
    pattern_parts = path_pattern.strip("/").split("/")
    path_parts = request_path.strip("/").split("/")

    if len(pattern_parts) != len(path_parts):
        return None

    params = {}
    for pattern_part, path_part in zip(pattern_parts, path_parts):
        if pattern_part.startswith(":"):
            params[pattern_part[1:]] = path_part

    return params if params else None


def normalize_path(path):
    """Normalize URL path."""
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    while "//" in path:
        path = path.replace("//", "/")
    return path.rstrip("/") or "/"


def get_client_ip(request_headers, remote_addr=None):
    """Get client IP from request."""
    forwarded = request_headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return remote_addr


def sanitize_filename(filename):
    """Sanitize filename for download."""
    import re

    return re.sub(r"[^\w\s.-]", "", filename).strip()


def build_response_headers(base_headers, content_type="application/json"):
    """Build response headers."""
    headers = {"Content-Type": content_type}
    if base_headers:
        headers.update(base_headers)
    return headers
