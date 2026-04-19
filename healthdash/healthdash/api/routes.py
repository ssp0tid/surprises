from flask import Blueprint, jsonify, request
from healthdash.models import Service, HealthCheck, db
from healthdash.api.validators import validate_service_data
from healthdash.utils.helpers import format_datetime
from healthdash.services.checker import perform_health_check

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


# Error handlers
@api_bp.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "validation_error", "message": str(e.description)}), 400


@api_bp.errorhandler(404)
def not_found(e):
    return jsonify({"error": "not_found", "message": str(e.description)}), 404


def serialize_service(service):
    """Serialize Service object to JSON"""
    return {
        "id": service.id,
        "name": service.name,
        "url": service.url,
        "method": service.method,
        "expected_status": service.expected_status,
        "check_interval": service.check_interval,
        "timeout": service.timeout,
        "is_active": service.is_active,
        "created_at": format_datetime(service.created_at),
        "updated_at": format_datetime(service.updated_at),
    }


def serialize_check(check):
    """Serialize HealthCheck object to JSON"""
    return {
        "id": check.id,
        "timestamp": format_datetime(check.timestamp),
        "is_up": check.is_up,
        "response_time": check.response_time,
        "status_code": check.status_code,
        "error_message": check.error_message,
    }


# Health check endpoint
@api_bp.route("/health", methods=["GET"])
def health_check():
    """API health check"""
    return jsonify({"status": "healthy", "version": "1.0"}), 200


# List all services
@api_bp.route("/services", methods=["GET"])
def list_services():
    """List all services"""
    services = Service.query.all()
    return jsonify([serialize_service(s) for s in services]), 200


# Create new service
@api_bp.route("/services", methods=["POST"])
@validate_service_data(required_fields=["name", "url"])
def create_service():
    """Create a new service"""
    data = request.get_json()

    service = Service(
        name=data["name"],
        url=data["url"],
        method=data.get("method", "GET").upper(),
        expected_status=data.get("expected_status", 200),
        check_interval=data.get("check_interval", 60),
        timeout=data.get("timeout", 10),
        is_active=data.get("is_active", True),
    )

    db.session.add(service)
    db.session.commit()

    return jsonify(serialize_service(service)), 201


# Get service details
@api_bp.route("/services/<int:service_id>", methods=["GET"])
def get_service(service_id):
    """Get service details"""
    service = Service.query.get(service_id)
    if not service:
        return jsonify({"error": "not_found", "message": "Service not found"}), 404

    return jsonify(serialize_service(service)), 200


# Update service
@api_bp.route("/services/<int:service_id>", methods=["PUT"])
@validate_service_data()
def update_service(service_id):
    """Update a service"""
    service = Service.query.get(service_id)
    if not service:
        return jsonify({"error": "not_found", "message": "Service not found"}), 404

    data = request.get_json()

    if "name" in data:
        service.name = data["name"]
    if "url" in data:
        service.url = data["url"]
    if "method" in data:
        service.method = data["method"].upper()
    if "expected_status" in data:
        service.expected_status = data["expected_status"]
    if "check_interval" in data:
        service.check_interval = data["check_interval"]
    if "timeout" in data:
        service.timeout = data["timeout"]
    if "is_active" in data:
        service.is_active = data["is_active"]

    db.session.commit()

    return jsonify(serialize_service(service)), 200


# Delete service
@api_bp.route("/services/<int:service_id>", methods=["DELETE"])
def delete_service(service_id):
    """Delete a service"""
    service = Service.query.get(service_id)
    if not service:
        return jsonify({"error": "not_found", "message": "Service not found"}), 404

    db.session.delete(service)
    db.session.commit()

    return jsonify({"message": "Service deleted successfully"}), 200


# Get check history
@api_bp.route("/services/<int:service_id>/checks", methods=["GET"])
def get_service_checks(service_id):
    """Get check history for a service with pagination"""
    service = Service.query.get(service_id)
    if not service:
        return jsonify({"error": "not_found", "message": "Service not found"}), 404

    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)

    # Ensure limits are within bounds
    limit = min(max(limit, 1), 1000)
    offset = max(offset, 0)

    total = service.checks.count()
    checks = (
        service.checks.order_by(HealthCheck.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return jsonify(
        {
            "service_id": service_id,
            "checks": [serialize_check(c) for c in checks],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    ), 200


# Get uptime/stats
@api_bp.route("/services/<int:service_id>/stats", methods=["GET"])
def get_service_stats(service_id):
    """Get uptime and stats for a service"""
    service = Service.query.get(service_id)
    if not service:
        return jsonify({"error": "not_found", "message": "Service not found"}), 404

    # Get last check
    last_check = service.checks.order_by(HealthCheck.timestamp.desc()).first()

    # Calculate stats from recent checks
    uptime_percentage = service.uptime_percentage
    avg_response_time_ms = service.avg_response_time
    total_checks = service.checks.count()

    return jsonify(
        {
            "service_id": service.id,
            "service_name": service.name,
            "uptime_percentage": uptime_percentage,
            "avg_response_time_ms": avg_response_time_ms,
            "total_checks": total_checks,
            "last_check": format_datetime(last_check.timestamp) if last_check else None,
            "last_status": last_check.is_up if last_check else None,
        }
    ), 200


# Trigger immediate check
@api_bp.route("/services/<int:service_id>/check", methods=["POST"])
def trigger_check(service_id):
    """Trigger an immediate health check"""
    service = Service.query.get(service_id)
    if not service:
        return jsonify({"error": "not_found", "message": "Service not found"}), 404

    check = perform_health_check(service_id)

    if check is None:
        return jsonify(
            {"error": "validation_error", "message": "Service is inactive"}
        ), 400

    return jsonify(serialize_check(check)), 200
