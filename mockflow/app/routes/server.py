"""Server control API routes."""

from flask import Blueprint, request, jsonify
from app.models import db, Project, ServerConfig, Endpoint
from app.services.mock_server import MockServer

server_bp = Blueprint("server", __name__)


@server_bp.route("/projects/<int:project_id>/server", methods=["GET"])
def get_server_status(project_id):
    """Get server status."""
    project = Project.query.get_or_404(project_id)

    config = ServerConfig.query.filter_by(project_id=project_id).first()
    if not config:
        config = ServerConfig(project_id=project_id)
        db.session.add(config)
        db.session.commit()

    status = {
        "project_id": project_id,
        "port": config.port,
        "host": config.host,
        "enabled": config.enabled,
        "cors_enabled": config.cors_enabled,
        "cors_origins": config.cors_origins,
        "log_requests": config.log_requests,
        "endpoint_count": Endpoint.query.filter_by(
            project_id=project_id, enabled=True
        ).count(),
    }

    if hasattr(server_bp, "mock_servers"):
        status["running"] = project_id in server_bp.mock_servers
    else:
        status["running"] = False

    return jsonify(status)


@server_bp.route("/projects/<int:project_id>/server/start", methods=["POST"])
def start_server(project_id):
    """Start the mock server."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json() or {}

    config = ServerConfig.query.filter_by(project_id=project_id).first()
    if not config:
        config = ServerConfig(project_id=project_id)
        db.session.add(config)
        db.session.commit()

    host = data.get("host", config.host)
    port = data.get("port", config.port)

    if not isinstance(port, int) or port < 1 or port > 65535:
        return jsonify({"error": "Port must be between 1 and 65535"}), 400

    endpoints = Endpoint.query.filter_by(project_id=project_id, enabled=True).all()
    if not endpoints:
        return jsonify({"error": "No enabled endpoints to serve"}), 400

    try:
        mock_srv = MockServer(
            host=host,
            port=port,
            project_id=project_id,
            cors_enabled=data.get("cors_enabled", config.cors_enabled),
            cors_origins=data.get("cors_origins", config.cors_origins),
        )
        mock_srv.start()

        if not hasattr(server_bp, "mock_servers"):
            server_bp.mock_servers = {}

        server_bp.mock_servers[project_id] = mock_srv
        config.enabled = True
        db.session.commit()

        return jsonify(
            {"success": True, "host": host, "port": port, "endpoints": len(endpoints)}
        )

    except OSError as e:
        return jsonify({"error": f"Failed to start server: {str(e)}"}), 500


@server_bp.route("/projects/<int:project_id>/server/stop", methods=["POST"])
def stop_server(project_id):
    """Stop the mock server."""
    project = Project.query.get_or_404(project_id)

    config = ServerConfig.query.filter_by(project_id=project_id).first()

    if hasattr(server_bp, "mock_servers") and project_id in server_bp.mock_servers:
        mock_srv = server_bp.mock_servers[project_id]
        mock_srv.stop()
        del server_bp.mock_servers[project_id]

    if config:
        config.enabled = False
        db.session.commit()

    return jsonify({"success": True, "stopped": True})


@server_bp.route("/projects/<int:project_id>/server/config", methods=["PUT"])
def update_server_config(project_id):
    """Update server configuration."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    config = ServerConfig.query.filter_by(project_id=project_id).first()
    if not config:
        config = ServerConfig(project_id=project_id)
        db.session.add(config)

    if "host" in data:
        config.host = data["host"]

    if "port" in data:
        port = data["port"]
        if not isinstance(port, int) or port < 1 or port > 65535:
            return jsonify({"error": "Port must be between 1 and 65535"}), 400
        config.port = port

    if "cors_enabled" in data:
        config.cors_enabled = data["cors_enabled"]

    if "cors_origins" in data:
        config.cors_origins = data["cors_origins"]

    if "log_requests" in data:
        config.log_requests = data["log_requests"]

    db.session.commit()
    return jsonify(config.to_dict())


@server_bp.route("/projects/<int:project_id>/server/stats", methods=["GET"])
def get_server_stats(project_id):
    """Get server statistics."""
    project = Project.query.get_or_404(project_id)

    from app.models import Log
    from sqlalchemy import func

    total_requests = Log.query.filter_by(project_id=project_id).count()
    matched_requests = Log.query.filter_by(project_id=project_id, matched=True).count()
    avg_response_time = (
        db.session.query(func.avg(Log.response_time_ms))
        .filter(Log.project_id == project_id)
        .scalar()
        or 0
    )

    config = ServerConfig.query.filter_by(project_id=project_id).first()

    return jsonify(
        {
            "project_id": project_id,
            "total_requests": total_requests,
            "matched_requests": matched_requests,
            "avg_response_time_ms": round(avg_response_time, 2),
            "enabled": config.enabled if config else False,
            "port": config.port if config else 8080,
        }
    )
