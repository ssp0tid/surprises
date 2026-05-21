"""Log API routes."""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from app.models import db, Log, Project

logs_bp = Blueprint("logs", __name__)


@logs_bp.route("/projects/<int:project_id>/logs", methods=["GET"])
def list_logs(project_id):
    """Get request logs with filtering."""
    project = Project.query.get_or_404(project_id)

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    per_page = min(per_page, 100)

    method = request.args.get("method", "").upper()
    endpoint_id = request.args.get("endpoint_id", None)
    status = request.args.get("status", None)
    matched = request.args.get("matched", None)
    path = request.args.get("path", "")
    start_date = request.args.get("start_date", None)
    end_date = request.args.get("end_date", None)

    query = Log.query.filter_by(project_id=project_id)

    if method:
        query = query.filter_by(method=method)

    if endpoint_id:
        query = query.filter_by(endpoint_id=int(endpoint_id))

    if status:
        query = query.filter_by(response_status=int(status))

    if matched is not None:
        query = query.filter_by(matched=matched.lower() == "true")

    if path:
        query = query.filter(Log.path.contains(path))

    if start_date:
        try:
            start = datetime.fromisoformat(start_date)
            query = query.filter(Log.created_at >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.fromisoformat(end_date)
            query = query.filter(Log.created_at <= end)
        except ValueError:
            pass

    query = query.order_by(Log.created_at.desc())
    total = query.count()
    logs = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify(
        {
            "logs": [l.to_dict() for l in logs],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@logs_bp.route("/logs/<int:log_id>", methods=["GET"])
def get_log(log_id):
    """Get single log entry details."""
    log = Log.query.get_or_404(log_id)
    return jsonify(log.to_dict())


@logs_bp.route("/projects/<int:project_id>/logs", methods=["DELETE"])
def clear_logs(project_id):
    """Clear logs for a project."""
    project = Project.query.get_or_404(project_id)

    clear_older_than = request.args.get("older_than", None)

    query = Log.query.filter_by(project_id=project_id)

    if clear_older_than:
        try:
            days = int(clear_older_than)
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Log.created_at < cutoff)
        except ValueError:
            pass

    query.delete()
    db.session.commit()

    return jsonify({"success": True, "deleted": True})


@logs_bp.route("/projects/<int:project_id>/logs/export", methods=["GET"])
def export_logs(project_id):
    """Export logs."""
    project = Project.query.get_or_404(project_id)

    limit = request.args.get("limit", 1000, type=int)
    limit = min(limit, 10000)

    logs = (
        Log.query.filter_by(project_id=project_id)
        .order_by(Log.created_at.desc())
        .limit(limit)
        .all()
    )

    return jsonify(
        {
            "logs": [l.to_dict() for l in logs],
            "exported_at": datetime.utcnow().isoformat(),
        }
    )
