"""Endpoint API routes."""

from flask import Blueprint, request, jsonify
from app.models import db, Endpoint, Response

endpoints_bp = Blueprint("endpoints", __name__)

VALID_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


def validate_path(path):
    """Validate endpoint path format."""
    if not path or not isinstance(path, str):
        return False, "Path is required"
    if len(path) > 500:
        return False, "Path must be 500 characters or less"
    if not path.startswith("/"):
        return False, "Path must start with /"
    return True, None


def validate_method(method):
    """Validate HTTP method."""
    if method.upper() not in VALID_METHODS:
        return False, f"Invalid method. Must be one of: {', '.join(VALID_METHODS)}"
    return True, None


@endpoints_bp.route("/projects/<int:project_id>/endpoints", methods=["GET"])
def list_endpoints(project_id):
    """List all endpoints in a project."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    per_page = min(per_page, 100)
    method = request.args.get("method", "").upper()
    enabled = request.args.get("enabled", None)

    query = Endpoint.query.filter_by(project_id=project_id)

    if method and method in VALID_METHODS:
        query = query.filter_by(method=method)

    if enabled is not None:
        query = query.filter_by(enabled=enabled.lower() == "true")

    query = query.order_by(Endpoint.priority.desc(), Endpoint.created_at.desc())
    total = query.count()
    endpoints = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify(
        {
            "endpoints": [e.to_dict() for e in endpoints],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@endpoints_bp.route("/endpoints/<int:endpoint_id>", methods=["GET"])
def get_endpoint(endpoint_id):
    """Get endpoint details with responses."""
    endpoint = Endpoint.query.get_or_404(endpoint_id)
    return jsonify(endpoint.to_dict(include_responses=True))


@endpoints_bp.route("/projects/<int:project_id>/endpoints", methods=["POST"])
def create_endpoint(project_id):
    """Create new endpoint."""
    endpoint_data = request.get_json()

    if not endpoint_data:
        return jsonify({"error": "Request body required"}), 400

    path = endpoint_data.get("path", "").strip()
    valid, error = validate_path(path)
    if not valid:
        return jsonify({"error": error}), 400

    method = endpoint_data.get("method", "GET").upper()
    valid, error = validate_method(method)
    if not valid:
        return jsonify({"error": error}), 400

    endpoint = Endpoint(
        project_id=project_id,
        path=path,
        method=method,
        description=endpoint_data.get("description", ""),
        enabled=endpoint_data.get("enabled", True),
        priority=endpoint_data.get("priority", 0),
        match_headers=endpoint_data.get("match_headers"),
        match_body=endpoint_data.get("match_body"),
        match_query=endpoint_data.get("match_query"),
    )
    db.session.add(endpoint)
    db.session.flush()

    default_response = Response(
        endpoint_id=endpoint.id,
        name=endpoint_data.get("response_name", "Default"),
        status_code=endpoint_data.get("status_code", 200),
        headers=endpoint_data.get("headers", {}),
        body=endpoint_data.get("body", ""),
        content_type=endpoint_data.get("content_type", "application/json"),
        delay_ms=endpoint_data.get("delay_ms", 0),
        is_default=True,
    )
    db.session.add(default_response)
    db.session.commit()

    return jsonify(endpoint.to_dict(include_responses=True)), 201


@endpoints_bp.route("/endpoints/<int:endpoint_id>", methods=["PUT"])
def update_endpoint(endpoint_id):
    """Update endpoint configuration."""
    endpoint = Endpoint.query.get_or_404(endpoint_id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    if "path" in data:
        path = data["path"].strip()
        valid, error = validate_path(path)
        if not valid:
            return jsonify({"error": error}), 400
        endpoint.path = path

    if "method" in data:
        method = data["method"].upper()
        valid, error = validate_method(method)
        if not valid:
            return jsonify({"error": error}), 400
        endpoint.method = method

    if "description" in data:
        endpoint.description = data["description"]

    if "enabled" in data:
        endpoint.enabled = bool(data["enabled"])

    if "priority" in data:
        try:
            endpoint.priority = int(data["priority"])
        except (ValueError, TypeError):
            return jsonify({"error": "Priority must be an integer"}), 400

    if "match_headers" in data:
        endpoint.match_headers = data["match_headers"]

    if "match_body" in data:
        endpoint.match_body = data["match_body"]

    if "match_query" in data:
        endpoint.match_query = data["match_query"]

    db.session.commit()
    return jsonify(endpoint.to_dict(include_responses=True))


@endpoints_bp.route("/endpoints/<int:endpoint_id>", methods=["DELETE"])
def delete_endpoint(endpoint_id):
    """Delete endpoint."""
    endpoint = Endpoint.query.get_or_404(endpoint_id)
    db.session.delete(endpoint)
    db.session.commit()
    return "", 204


@endpoints_bp.route("/endpoints/reorder", methods=["PUT"])
def reorder_endpoints():
    """Update endpoint priority order."""
    data = request.get_json()

    if not data or "endpoints" not in data:
        return jsonify({"error": "endpoints array required"}), 400

    endpoints = data["endpoints"]
    for item in endpoints:
        endpoint_id = item.get("id")
        priority = item.get("priority")
        if endpoint_id and priority is not None:
            endpoint = Endpoint.query.get(endpoint_id)
            if endpoint:
                endpoint.priority = priority

    db.session.commit()
    return jsonify({"success": True})


@endpoints_bp.route("/endpoints/<int:endpoint_id>/test", methods=["POST"])
def test_endpoint(endpoint_id):
    """Test endpoint definition."""
    endpoint = Endpoint.query.get_or_404(endpoint_id)
    test_request = request.get_json() or {}

    response = endpoint.responses[0] if endpoint.responses else None

    if not response:
        return jsonify({"matched": False, "error": "No response configured"}), 404

    from app.services.matcher import RequestMatcher

    matcher = RequestMatcher(None)
    matched_response = matcher.match_response(endpoint, test_request)

    return jsonify(
        {
            "matched": matched_response is not None,
            "response": matched_response.to_dict() if matched_response else None,
            "endpoint": endpoint.to_dict(),
        }
    )
