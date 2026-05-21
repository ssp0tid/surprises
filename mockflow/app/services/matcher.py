"""Request matching logic for mock endpoints."""

import re
import json
import uuid
import time
from datetime import datetime


class RequestMatcher:
    """Matches incoming requests to configured endpoints."""

    def __init__(self, app=None):
        self.app = app

    def match_endpoint(
        self, endpoints, method, path, headers=None, query_params=None, body=None
    ):
        """Find matching endpoint from a list of endpoints.

        Returns tuple of (endpoint, response) or (None, None) if no match.
        """
        sorted_endpoints = sorted(
            [e for e in endpoints if e.enabled],
            key=lambda e: e.priority or 0,
            reverse=True,
        )

        for endpoint in sorted_endpoints:
            if endpoint.method != method:
                continue

            if self._path_matches(endpoint.path, path):
                if self._conditions_match(endpoint, headers, query_params, body):
                    response = self._select_response(
                        endpoint, headers, query_params, body
                    )
                    return endpoint, response

        return None, None

    def _path_matches(self, pattern, path):
        """Check if request path matches endpoint pattern."""
        if pattern == path:
            return True

        pattern_parts = pattern.strip("/").split("/")
        path_parts = path.strip("/").split("/")

        if len(pattern_parts) != len(path_parts):
            return False

        for pp, p in zip(path_parts, pattern_parts):
            if pp == p:
                continue
            if p.startswith(":"):
                continue
            if p.startswith("*"):
                return True

        return True

    def _conditions_match(self, endpoint, headers, query_params, body):
        """Check if request matches endpoint conditions."""
        if endpoint.match_headers:
            if not self._headers_match(endpoint.match_headers, headers):
                return False

        if endpoint.match_query:
            if not self._query_match(endpoint.match_query, query_params):
                return False

        if endpoint.match_body:
            if not self._body_match(endpoint.match_body, body):
                return False

        return True

    def _headers_match(self, conditions, headers):
        """Check header conditions."""
        if not headers:
            return False
        for key, value in conditions.items():
            if headers.get(key) != value:
                return False
        return True

    def _query_match(self, conditions, query_params):
        """Check query parameter conditions."""
        if not query_params:
            return False
        for key, value in conditions.items():
            if query_params.get(key) != value:
                return False
        return True

    def _body_match(self, conditions, body):
        """Check body content conditions."""
        if not body:
            return False
        try:
            body_data = json.loads(body) if isinstance(body, str) else body
            for key, value in conditions.items():
                if body_data.get(key) != value:
                    return False
        except (json.JSONDecodeError, TypeError):
            return False
        return True

    def _select_response(self, endpoint, headers, query_params, body):
        """Select appropriate response based on conditions."""
        for response in endpoint.responses:
            if not response.is_default and response.conditions:
                if self._response_conditions_match(
                    response.conditions, headers, query_params, body
                ):
                    return response

        for response in endpoint.responses:
            if response.is_default:
                return response

        return endpoint.responses[0] if endpoint.responses else None

    def _response_conditions_match(self, conditions, headers, query_params, body):
        """Check if response conditions are met."""
        if not conditions:
            return True

        if "headers" in conditions:
            if not self._headers_match(conditions["headers"], headers):
                return False

        if "query" in conditions:
            if not self._query_match(conditions["query"], query_params):
                return False

        if "body" in conditions:
            if not self._body_match(conditions["body"], body):
                return False

        if "status" in conditions:
            return True

        return True

    def match_response(self, endpoint, request_data):
        """Match response for a test request."""
        method = request_data.get("method", "GET")
        path = request_data.get("path", "/")
        headers = request_data.get("headers", {})
        query_params = request_data.get("query_params", {})
        body = request_data.get("body")

        _, response = self.match_endpoint(
            [endpoint], method, path, headers, query_params, body
        )
        return response


class DynamicResolver:
    """Resolves dynamic variables in response body."""

    VARIABLE_PATTERN = re.compile(r"\{\{(\w+(?:\.\w+)*)\}\}")

    def __init__(self, request_data):
        self.request_data = request_data

    def resolve(self, body):
        """Resolve all dynamic variables in response body."""
        if not isinstance(body, str):
            return body

        def replace_var(m):
            var_path = m.group(1)
            return self._get_variable(var_path, m)

        resolved = self.VARIABLE_PATTERN.sub(replace_var, body)

        try:
            return json.loads(resolved)
        except (json.JSONDecodeError, ValueError):
            return resolved

    def _get_variable(self, var_path, match=None):
        """Get variable value by path."""
        parts = var_path.split(".")

        if parts[0] == "uuid":
            return str(uuid.uuid4())

        if parts[0] == "timestamp":
            if len(parts) > 1 and parts[1] == "unix":
                return int(time.time())
            return datetime.utcnow().isoformat()

        if parts[0] == "random":
            if len(parts) < 2:
                return str(uuid.uuid4())[:8]
            if parts[1] == "number":
                return str(random_int(parts[2] if len(parts) > 2 else "100"))
            if parts[1] == "string":
                return random_string(parts[2] if len(parts) > 2 else "8")

        if parts[0] == "request":
            return self._get_nested(self.request_data, parts[1:])

        return match.group(0) if match else "{{" + var_path + "}}"

    def _get_nested(self, data, keys):
        """Get nested value from dict."""
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key, "")
            elif isinstance(data, list) and key.isdigit():
                data = data[int(key)] if int(key) < len(data) else ""
            else:
                return ""
        return str(data) if data is not None else ""


def random_int(max_val=100):
    import random

    return random.randint(1, int(max_val))


def random_string(length=8):
    import random
    import string

    return "".join(random.choices(string.ascii_letters + string.digits, k=int(length)))
