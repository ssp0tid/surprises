from flask import request, jsonify
from functools import wraps


def validate_service_data(required_fields=None):
    """Validate incoming service data"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()

            if not data:
                return jsonify(
                    {"error": "validation_error", "message": "Request body required"}
                ), 400

            if required_fields:
                missing = [f for f in required_fields if f not in data]
                if missing:
                    return jsonify(
                        {
                            "error": "validation_error",
                            "message": f"Missing required fields: {', '.join(missing)}",
                        }
                    ), 400

            # URL validation
            if "url" in data:
                if not data["url"].startswith(("http://", "https://")):
                    return jsonify(
                        {
                            "error": "validation_error",
                            "message": "URL must start with http:// or https://",
                        }
                    ), 400

            # Interval validation
            if "check_interval" in data:
                interval = data["check_interval"]
                if not isinstance(interval, int) or interval < 10 or interval > 3600:
                    return jsonify(
                        {
                            "error": "validation_error",
                            "message": "check_interval must be between 10 and 3600 seconds",
                        }
                    ), 400

            # Timeout validation
            if "timeout" in data:
                timeout = data["timeout"]
                if not isinstance(timeout, int) or timeout < 1 or timeout > 60:
                    return jsonify(
                        {
                            "error": "validation_error",
                            "message": "timeout must be between 1 and 60 seconds",
                        }
                    ), 400

            # HTTP method validation
            if "method" in data:
                method = data["method"].upper()
                if method not in ("GET", "POST", "HEAD"):
                    return jsonify(
                        {
                            "error": "validation_error",
                            "message": "method must be GET, POST, or HEAD",
                        }
                    ), 400

            return f(*args, **kwargs)

        return decorated_function

    return decorator
