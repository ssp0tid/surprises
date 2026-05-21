"""Project API routes."""

from flask import Blueprint, request, jsonify
from app.models import db, Project, Endpoint, ServerConfig

projects_bp = Blueprint("projects", __name__)

VALID_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


@projects_bp.route("/projects", methods=["GET"])
def list_projects():
    """List all projects with pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    query = Project.query.order_by(Project.updated_at.desc())
    total = query.count()
    projects = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify(
        {
            "projects": [p.to_dict() for p in projects],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@projects_bp.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):
    """Get single project with endpoints."""
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())


@projects_bp.route("/projects", methods=["POST"])
def create_project():
    """Create new project."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if len(name) > 255:
        return jsonify({"error": "Name must be 255 characters or less"}), 400

    project = Project(
        name=name,
        description=data.get("description", ""),
        base_url=data.get("base_url", ""),
        settings=data.get("settings", {}),
    )
    db.session.add(project)
    db.session.flush()

    config = ServerConfig(
        project_id=project.id,
        port=data.get("port", 8080),
        host=data.get("host", "0.0.0.0"),
        cors_enabled=data.get("cors_enabled", True),
        cors_origins=data.get("cors_origins", "*"),
        log_requests=data.get("log_requests", True),
    )
    db.session.add(config)
    db.session.commit()

    return jsonify(project.to_dict()), 201


@projects_bp.route("/projects/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    """Update project details."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    if "name" in data:
        name = data["name"].strip()
        if not name:
            return jsonify({"error": "Name cannot be empty"}), 400
        if len(name) > 255:
            return jsonify({"error": "Name must be 255 characters or less"}), 400
        project.name = name

    if "description" in data:
        project.description = data["description"]

    if "base_url" in data:
        project.base_url = data["base_url"]

    if "settings" in data:
        project.settings = data["settings"]

    db.session.commit()
    return jsonify(project.to_dict())


@projects_bp.route("/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    """Delete project and all associated data."""
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return "", 204


@projects_bp.route("/projects/<int:project_id>/export", methods=["GET"])
def export_project(project_id):
    """Export project configuration."""
    project = Project.query.get_or_404(project_id)

    export_data = {
        "project": project.to_dict(),
        "endpoints": [e.to_dict(include_responses=True) for e in project.endpoints],
        "version": "1.0",
    }
    return jsonify(export_data)


@projects_bp.route("/projects/import/json", methods=["POST"])
def import_project():
    """Import project from JSON."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    project_name = data.get("project", {}).get("name", "").strip()
    if not project_name:
        return jsonify({"error": "Project name required"}), 400

    project = Project(
        name=project_name,
        description=data.get("project", {}).get("description", ""),
        base_url=data.get("project", {}).get("base_url", ""),
    )
    db.session.add(project)
    db.session.flush()

    endpoints_data = data.get("endpoints", [])
    for ep_data in endpoints_data:
        endpoint = Endpoint(
            project_id=project.id,
            path=ep_data.get("path", ""),
            method=ep_data.get("method", "GET").upper(),
            description=ep_data.get("description", ""),
            enabled=ep_data.get("enabled", True),
            priority=ep_data.get("priority", 0),
        )
        if not endpoint.path or endpoint.method not in VALID_METHODS:
            continue
        db.session.add(endpoint)
        db.session.flush()

        responses_data = ep_data.get("responses", [])
        for resp_data in responses_data:
            from app.models import Response

            response = Response(
                endpoint_id=endpoint.id,
                name=resp_data.get("name", "Default"),
                status_code=resp_data.get("status_code", 200),
                headers=resp_data.get("headers", {}),
                body=resp_data.get("body", ""),
                content_type=resp_data.get("content_type", "application/json"),
                delay_ms=resp_data.get("delay_ms", 0),
                is_default=resp_data.get("is_default", True),
            )
            db.session.add(response)

    config = ServerConfig(project_id=project.id)
    db.session.add(config)
    db.session.commit()

    return jsonify(project.to_dict()), 201
