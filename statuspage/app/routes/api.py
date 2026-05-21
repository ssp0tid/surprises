from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from app.models import Component, ComponentGroup, Incident, Organization
from app.utils.helpers import generate_chart_data

api_bp = Blueprint("api", __name__)


@api_bp.route("/status/<org_slug>")
def status_json(org_slug):
    org = Organization.query.filter_by(slug=org_slug).first()
    if not org:
        return jsonify({"error": "Organization not found"}), 404

    overall_status = org.get_overall_status()

    components = (
        Component.query.filter_by(organization_id=org.id, is_enabled=True)
        .order_by(Component.display_order)
        .all()
    )

    component_list = []
    for comp in components:
        latest = comp.latest_result()
        component_list.append(
            {
                "id": comp.id,
                "name": comp.name,
                "status": comp.get_status(),
                "uptime_24h": round(comp.get_uptime(1), 2),
                "uptime_7d": round(comp.get_uptime(7), 2),
                "uptime_30d": round(comp.get_uptime(30), 2),
                "response_time_ms": latest.response_time_ms if latest else None,
            }
        )

    active_incidents = Incident.query.filter(
        Incident.organization_id == org.id, Incident.status != "resolved"
    ).all()

    incident_list = []
    for inc in active_incidents:
        incident_list.append(
            {
                "id": inc.id,
                "title": inc.title,
                "severity": inc.severity,
                "status": inc.status,
                "created_at": inc.created_at.isoformat(),
            }
        )

    return jsonify(
        {
            "organization": org.name,
            "status": overall_status,
            "components": component_list,
            "incidents": incident_list,
            "last_updated": datetime.utcnow().isoformat(),
        }
    )


@api_bp.route("/components/<org_slug>")
def components_json(org_slug):
    org = Organization.query.filter_by(slug=org_slug).first()
    if not org:
        return jsonify({"error": "Organization not found"}), 404

    components = Component.query.filter_by(
        organization_id=org.id, is_enabled=True
    ).all()

    result = []
    for comp in components:
        result.append(
            {
                "id": comp.id,
                "name": comp.name,
                "description": comp.description,
                "type": comp.check_type,
                "status": comp.get_status(),
                "uptime_24h": round(comp.get_uptime(1), 2),
                "uptime_7d": round(comp.get_uptime(7), 2),
                "uptime_30d": round(comp.get_uptime(30), 2),
            }
        )

    return jsonify({"components": result})


@api_bp.route("/component/<int:component_id>/history")
def component_history(component_id):
    hours = request.args.get("hours", 24, type=int)
    hours = min(hours, 168)

    comp = Component.query.get(component_id)
    if not comp:
        return jsonify({"error": "Component not found"}), 404

    history = comp.get_history(hours)

    result = []
    for check in history:
        result.append(
            {
                "status": check.status,
                "response_time_ms": check.response_time_ms,
                "status_code": check.status_code,
                "checked_at": check.checked_at.isoformat(),
            }
        )

    return jsonify({"component": comp.name, "hours": hours, "history": result})


@api_bp.route("/badge/<org_slug>")
def badge(org_slug):
    from flask import make_response

    org = Organization.query.filter_by(slug=org_slug).first()
    if not org:
        return make_response("Not Found", 404)

    status = org.get_overall_status()

    colors = {"operational": "22c55e", "degraded": "f59e0b", "down": "ef4444"}
    color = colors.get(status, "6b7280")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="120" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="a">
    <rect width="120" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#a)">
    <rect width="60" height="20" fill="#555"/>
    <rect x="60" width="60" height="20" fill="#{color}"/>
    <path d="M60 0h60v20H60z" fill="url(#b)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="sans-serif" font-size="11">
    <text x="30" y="15" fill="#010101" fill-opacity=".3">status</text>
    <text x="90" y="15" fill="#010101" fill-opacity=".3">{status}</text>
  </g>
</svg>"""

    response = make_response(svg)
    response.content_type = "image/svg+xml"
    return response
