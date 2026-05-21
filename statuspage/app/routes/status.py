from datetime import datetime, timedelta

from flask import Blueprint, render_template, abort

from app import db
from app.models import (
    Component,
    ComponentGroup,
    Incident,
    IncidentTimeline,
    Organization,
)
from app.utils.helpers import generate_chart_data

status_bp = Blueprint("status", __name__)


def get_organization_or_404(org_slug):
    org = Organization.query.filter_by(slug=org_slug).first()
    if not org:
        abort(404)
    return org


@status_bp.route("/<org_slug>")
def page(org_slug):
    org = get_organization_or_404(org_slug)

    overall_status = org.get_overall_status()

    groups = (
        ComponentGroup.query.filter_by(organization_id=org.id)
        .order_by(ComponentGroup.display_order)
        .all()
    )

    ungrouped_components = (
        Component.query.filter_by(organization_id=org.id, group_id=None)
        .filter(Component.is_enabled == True)
        .order_by(Component.display_order)
        .all()
    )

    all_components = []
    for group in groups:
        group_components = (
            Component.query.filter_by(organization_id=org.id, group_id=group.id)
            .filter(Component.is_enabled == True)
            .order_by(Component.display_order)
            .all()
        )
        for comp in group_components:
            comp.current_status = comp.get_status()
            comp.uptime_30d = comp.get_uptime(30)
        group.components_list = group_components
        all_components.extend(group.components_list)

    for comp in ungrouped_components:
        comp.current_status = comp.get_status()
        comp.uptime_30d = comp.get_uptime(30)
    all_components.extend(ungrouped_components)

    active_incidents = (
        Incident.query.filter(
            Incident.organization_id == org.id, Incident.status != "resolved"
        )
        .order_by(Incident.created_at.desc())
        .all()
    )

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_incidents = (
        Incident.query.filter(
            Incident.organization_id == org.id,
            Incident.status == "resolved",
            Incident.resolved_at >= thirty_days_ago,
        )
        .order_by(Incident.created_at.desc())
        .all()
    )

    branding = org.get_branding()

    return render_template(
        "status/page.html",
        organization=org,
        overall_status=overall_status,
        groups=groups,
        ungrouped_components=ungrouped_components,
        active_incidents=active_incidents,
        recent_incidents=recent_incidents,
        branding=branding,
    )


@status_bp.route("/<org_slug>/history")
def history(org_slug):
    org = get_organization_or_404(org_slug)

    overall_status = org.get_overall_status()

    components = (
        Component.query.filter_by(organization_id=org.id)
        .filter(Component.is_enabled == True)
        .order_by(Component.display_order)
        .all()
    )

    component_data = []
    for comp in components:
        history_24h = comp.get_history(24)
        history_7d = comp.get_history(168)

        chart_data_24h = generate_chart_data(history_24h, buckets=24)
        chart_data_7d = generate_chart_data(history_7d, buckets=24)

        component_data.append(
            {
                "component": comp,
                "status": comp.get_status(),
                "uptime_24h": comp.get_uptime(1),
                "uptime_7d": comp.get_uptime(7),
                "uptime_30d": comp.get_uptime(30),
                "chart_24h": chart_data_24h,
                "chart_7d": chart_data_7d,
            }
        )

    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
    past_incidents = (
        Incident.query.filter(
            Incident.organization_id == org.id,
            Incident.status == "resolved",
            Incident.resolved_at >= ninety_days_ago,
        )
        .order_by(Incident.created_at.desc())
        .all()
    )

    enabled_components = [c for c in components if c.is_enabled]
    if enabled_components:
        overall_uptime_24h = sum(c.get_uptime(1) for c in enabled_components) / len(
            enabled_components
        )
        overall_uptime_7d = sum(c.get_uptime(7) for c in enabled_components) / len(
            enabled_components
        )
        overall_uptime_30d = sum(c.get_uptime(30) for c in enabled_components) / len(
            enabled_components
        )
    else:
        overall_uptime_24h = 100.0
        overall_uptime_7d = 100.0
        overall_uptime_30d = 100.0

    branding = org.get_branding()

    return render_template(
        "status/history.html",
        organization=org,
        overall_status=overall_status,
        component_data=component_data,
        past_incidents=past_incidents,
        overall_uptime_24h=overall_uptime_24h,
        overall_uptime_7d=overall_uptime_7d,
        overall_uptime_30d=overall_uptime_30d,
        branding=branding,
    )


@status_bp.route("/<org_slug>/incident/<int:incident_id>")
def incident(org_slug, incident_id):
    """Public Incident Detail - Shows incident with timeline."""
    org = get_organization_or_404(org_slug)

    # Get incident for this organization
    incident = Incident.query.filter_by(id=incident_id, organization_id=org.id).first()
    if not incident:
        abort(404)

    # Get timeline events ordered chronologically (oldest first for display)
    timeline = incident.timeline.order_by(IncidentTimeline.created_at.asc()).all()

    # Get branding for template customization
    branding = org.get_branding()

    return render_template(
        "status/incident.html",
        organization=org,
        incident=incident,
        timeline=timeline,
        branding=branding,
    )
