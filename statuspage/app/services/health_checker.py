import json
import socket
import subprocess
import time
from urllib.parse import urlparse

import requests

from app import db
from app.models import CheckResult


def check_http_component(component):
    """Perform HTTP health check for a component.

    Args:
        component: Component model instance

    Returns:
        CheckResult: Result of the health check
    """
    check_url = component.check_url
    check_method = component.check_method or "GET"
    check_timeout = component.check_timeout or 30
    check_expected_status = component.check_expected_status or 200
    check_headers = component.check_headers

    headers = {}
    if check_headers:
        try:
            headers = (
                json.loads(check_headers)
                if isinstance(check_headers, str)
                else check_headers
            )
        except (json.JSONDecodeError, TypeError):
            headers = {}

    status = "down"
    response_time = 0
    status_code = None
    error_message = None

    try:
        start_time = time.time()

        # Make the HTTP request
        if check_method.upper() == "GET":
            response = requests.get(check_url, headers=headers, timeout=check_timeout)
        elif check_method.upper() == "POST":
            response = requests.post(check_url, headers=headers, timeout=check_timeout)
        elif check_method.upper() == "HEAD":
            response = requests.head(check_url, headers=headers, timeout=check_timeout)
        else:
            response = requests.request(
                check_method.upper(), check_url, headers=headers, timeout=check_timeout
            )

        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        status_code = response.status_code

        # Determine status based on response
        if status_code == check_expected_status:
            if response_time < 1000:
                status = "operational"
            else:
                status = "degraded"
        else:
            status = "down"
            error_message = (
                f"Expected status {check_expected_status}, got {status_code}"
            )

    except requests.Timeout:
        error_message = "Request timed out"
        status = "down"
    except requests.ConnectionError as e:
        error_message = f"Connection error: {str(e)}"
        status = "down"
    except requests.RequestException as e:
        error_message = f"Request error: {str(e)}"
        status = "down"
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        status = "down"

    # Create and save CheckResult
    result = CheckResult(
        component_id=component.id,
        status=status,
        response_time_ms=int(response_time),
        status_code=status_code,
        error_message=error_message,
    )
    db.session.add(result)
    db.session.commit()

    return result


def check_tcp_component(component):
    """Perform TCP port health check for a component.

    Args:
        component: Component model instance

    Returns:
        CheckResult: Result of the health check
    """
    check_url = component.check_url
    check_timeout = component.check_timeout or 30

    status = "down"
    response_time = 0
    status_code = None
    error_message = None

    try:
        # Parse host and port from check_url (format: host:port)
        parsed = urlparse(f"//{check_url}")
        host = parsed.hostname or parsed.path.split(":")[0]
        port = (
            parsed.port or int(parsed.path.split(":")[1]) if ":" in parsed.path else 80
        )

        start_time = time.time()

        # Create socket and attempt connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(check_timeout)
        sock.connect((host, port))
        sock.close()

        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds

        status = "operational"

    except socket.timeout:
        error_message = "Connection timed out"
        status = "down"
    except socket.error as e:
        error_message = f"Socket error: {str(e)}"
        status = "down"
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        status = "down"

    # Create and save CheckResult
    result = CheckResult(
        component_id=component.id,
        status=status,
        response_time_ms=int(response_time),
        status_code=status_code,
        error_message=error_message,
    )
    db.session.add(result)
    db.session.commit()

    return result


def check_ping_component(component):
    """Perform ICMP ping health check for a component.

    Note: Requires root/admin privileges on most systems.

    Args:
        component: Component model instance

    Returns:
        CheckResult: Result of the health check
    """
    check_url = component.check_url

    status = "down"
    response_time = 0
    status_code = None
    error_message = None

    try:
        # Parse host from check_url
        parsed = urlparse(f"//{check_url}")
        host = parsed.hostname or parsed.path.split(":")[0]

        start_time = time.time()

        # Run ping command
        result = subprocess.run(
            ["ping", "-c", "1", host],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds

        if result.returncode == 0:
            status = "operational"
        else:
            error_message = f"Ping failed with return code {result.returncode}"
            status = "down"

    except subprocess.TimeoutExpired:
        error_message = "Ping command timed out"
        status = "down"
    except FileNotFoundError:
        error_message = "Ping command not found"
        status = "down"
    except PermissionError:
        error_message = "Permission denied - ping requires root/admin privileges"
        status = "down"
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        status = "down"

    # Create and save CheckResult
    result = CheckResult(
        component_id=component.id,
        status=status,
        response_time_ms=int(response_time),
        status_code=status_code,
        error_message=error_message,
    )
    db.session.add(result)
    db.session.commit()

    return result


def check_component(component):
    """Main dispatcher for component health checks.

    Routes to the appropriate check function based on component.check_type.

    Args:
        component: Component model instance

    Returns:
        CheckResult: Result of the health check
    """
    check_type = component.check_type or "http"

    try:
        if check_type == "http":
            return check_http_component(component)
        elif check_type == "tcp":
            return check_tcp_component(component)
        elif check_type == "ping":
            return check_ping_component(component)
        else:
            # Unknown check type - return down status
            error_message = f"Unknown check type: {check_type}"
            result = CheckResult(
                component_id=component.id,
                status="down",
                response_time_ms=0,
                status_code=None,
                error_message=error_message,
            )
            db.session.add(result)
            db.session.commit()
            return result

    except Exception as e:
        # Handle any unexpected exceptions gracefully
        error_message = f"Check failed with error: {str(e)}"
        result = CheckResult(
            component_id=component.id,
            status="down",
            response_time_ms=0,
            status_code=None,
            error_message=error_message,
        )
        db.session.add(result)
        db.session.commit()
        return result
