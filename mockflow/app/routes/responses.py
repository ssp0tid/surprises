"""Response API routes."""

from flask import Blueprint, request, jsonify
from app.models import db, Response, Endpoint

responses_bp = Blueprint("responses", __name__)

VALID_STATUS_CODES = [200, 201, 204, 400, 401, 403, 404, 500, 502, 503]
VALID_CONTENT_TYPES = [
    "application/json",
    "application/xml",
    "text/plain",
    "text/html",
    "application/octet-stream",
    "multipart/form-data",
]


@responses_bp.route("/endpoints/<int:endpoint_id>/responses", methods=["GET"])
def list_responses(endpoint_id):
    """List all responses for an endpoint."""
    endpoint = Endpoint.query.get_or_404(endpoint_id)
    responses = (
        Response.query.filter_by(endpoint_id=endpoint_id)
        .order_by(Response.is_default.desc())
        .all()
    )
    return jsonify({"responses": [r.to_dict() for r in responses]})


@responses_bp.route("/responses/<int:response_id>", methods=["GET"])
def get_response(response_id):
    """Get response definition."""
    response = Response.query.get_or_404(response_id)
    return jsonify(response.to_dict())


@responses_bp.route("/endpoints/<int:endpoint_id>/responses", methods=["POST"])
def create_response(endpoint_id):
    """Add new response."""
    endpoint = Endpoint.query.get_or_404(endpoint_id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if len(name) > 255:
        return jsonify({"error": "Name must be 255 characters or less"}), 400

    status_code = data.get("status_code", 200)
    if status_code not in VALID_STATUS_CODES:
        return jsonify(
            {
                "error": f"Invalid status code. Must be one of: {', '.join(map(str, VALID_STATUS_CODES))}"
            }
        ), 400

    content_type = data.get("content_type", "application/json")
    if content_type not in VALID_CONTENT_TYPES:
        return jsonify({"error": f"Invalid content type"}), 400

    delay_ms = data.get("delay_ms", 0)
    if not isinstance(delay_ms, int) or delay_ms < 0 or delay_ms > 30000:
        return jsonify({"error": "Delay must be between 0 and 30000 ms"}), 400

    response = Response(
        endpoint_id=endpoint_id,
        name=name,
        status_code=status_code,
        headers=data.get("headers", {}),
        body=data.get("body", ""),
        content_type=content_type,
        delay_ms=delay_ms,
        is_default=data.get("is_default", False),
        conditions=data.get("conditions"),
    )
    db.session.add(response)
    db.session.commit()

    return jsonify(response.to_dict()), 201


@responses_bp.route("/responses/<int:response_id>", methods=["PUT"])
def update_response(response_id):
    """Update response."""
    response = Response.query.get_or_404(response_id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    if "name" in data:
        name = data["name"].strip()
        if not name:
            return jsonify({"error": "Name cannot be empty"}), 400
        if len(name) > 255:
            return jsonify({"error": "Name must be 255 characters or less"}), 400
        response.name = name

    if "status_code" in data:
        status_code = data["status_code"]
        if status_code not in VALID_STATUS_CODES:
            return jsonify({"error": f"Invalid status code"}), 400
        response.status_code = status_code

    if "headers" in data:
        response.headers = data["headers"]

    if "body" in data:
        response.body = data["body"]

    if "content_type" in data:
        content_type = data["content_type"]
        if content_type not in VALID_CONTENT_TYPES:
            return jsonify({"error": "Invalid content type"}), 400
        response.content_type = content_type

    if "delay_ms" in data:
        delay_ms = data["delay_ms"]
        if not isinstance(delay_ms, int) or delay_ms < 0 or delay_ms > 30000:
            return jsonify({"error": "Delay must be between 0 and 30000 ms"}), 400
        response.delay_ms = delay_ms

    if "conditions" in data:
        response.conditions = data["conditions"]

    db.session.commit()
    return jsonify(response.to_dict())


@responses_bp.route("/responses/<int:response_id>", methods=["DELETE"])
def delete_response(response_id):
    """Delete response."""
    response = Response.query.get_or_404(response_id)

    if response.is_default:
        return jsonify({"error": "Cannot delete default response"}), 400

    db.session.delete(response)
    db.session.commit()
    return "", 204


@responses_bp.route("/responses/<int:response_id>/set-default", methods=["PUT"])
def set_default_response(response_id):
    """Mark response as default."""
    response = Response.query.get_or_404(response_id)

    Response.query.filter_by(endpoint_id=response.endpoint_id).update(
        {"is_default": False}
    )
    response.is_default = True
    db.session.commit()

    endpoint = Endpoint.query.get(response.endpoint_id)
    return jsonify(endpoint.to_dict(include_responses=True))
