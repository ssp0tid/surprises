import requests
from datetime import datetime
from healthdash.models import HealthCheck, Service, db


def perform_health_check(service_id):
    """Execute health check for a service"""
    service = Service.query.get(service_id)
    if not service or not service.is_active:
        return None

    start_time = None
    error_message = None
    status_code = None
    is_up = False
    response_time = None

    try:
        start_time = datetime.utcnow()

        response = requests.request(
            method=service.method,
            url=service.url,
            timeout=service.timeout,
            allow_redirects=True,
        )

        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        status_code = response.status_code
        is_up = status_code == service.expected_status

    except requests.Timeout:
        error_message = "Request timeout"
        response_time = service.timeout * 1000
    except requests.ConnectionError as e:
        error_message = f"Connection error: {str(e)[:200]}"
    except requests.RequestException as e:
        error_message = f"Request error: {str(e)[:200]}"
    except Exception as e:
        error_message = f"Unexpected error: {str(e)[:200]}"

    # Save check result
    check = HealthCheck(
        service_id=service.id,
        is_up=is_up,
        response_time=response_time,
        status_code=status_code,
        error_message=error_message,
    )

    db.session.add(check)
    db.session.commit()

    return check
