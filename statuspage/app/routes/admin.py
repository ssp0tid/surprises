import json

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.forms import (
    ComponentForm,
    ComponentGroupForm,
    IncidentForm,
    IncidentUpdateForm,
    SettingsForm,
)
from app.models import (
    Component,
    ComponentGroup,
    Incident,
    IncidentTimeline,
    Organization,
)

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@login_required
def index():
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    org = current_user.organization
    components = (
        Component.query.filter_by(organization_id=org.id)
        .order_by(Component.display_order)
        .all()
    )
    incidents = (
        Incident.query.filter(
            Incident.organization_id == org.id, Incident.status != "resolved"
        )
        .order_by(Incident.created_at.desc())
        .limit(5)
        .all()
    )

    for comp in components:
        comp.latest_status = comp.get_status()
        comp.uptime_24h = comp.get_uptime(1)
        comp.uptime_30d = comp.get_uptime(30)

    return render_template(
        "admin/dashboard.html", components=components, incidents=incidents
    )


@admin_bp.route("/components")
@login_required
def components():
    org = current_user.organization
    groups = (
        ComponentGroup.query.filter_by(organization_id=org.id)
        .order_by(ComponentGroup.display_order)
        .all()
    )
    components = (
        Component.query.filter_by(organization_id=org.id)
        .order_by(Component.display_order)
        .all()
    )

    return render_template(
        "admin/components.html", groups=groups, components=components
    )


@admin_bp.route("/components/new", methods=["GET", "POST"])
@login_required
def component_new():
    form = ComponentForm()
    org = current_user.organization

    form.group_id.choices = [(0, "No Group")]
    for group in ComponentGroup.query.filter_by(organization_id=org.id).all():
        form.group_id.choices.append((group.id, group.name))

    if form.validate_on_submit():
        comp = Component(
            organization_id=org.id,
            name=form.name.data,
            description=form.description.data,
            group_id=form.group_id.data if form.group_id.data != 0 else None,
            check_type=form.check_type.data,
            check_url=form.check_url.data,
            check_method=form.check_method.data,
            check_timeout=form.check_timeout.data,
            check_interval=form.check_interval.data,
            check_expected_status=form.check_expected_status.data,
            check_headers=form.check_headers.data,
            is_enabled=form.is_enabled.data,
            display_order=form.display_order.data or 0,
        )
        db.session.add(comp)
        db.session.commit()
        flash("Component created successfully", "success")
        return redirect(url_for("admin.components"))

    form.group_id.choices.insert(0, (0, "No Group"))
    return render_template("admin/component_form.html", form=form, action="Create")


@admin_bp.route("/components/<int:id>/edit", methods=["GET", "POST"])
@login_required
def component_edit(id):
    comp = Component.query.get_or_404(id)
    if comp.organization_id != current_user.organization_id:
        flash("Access denied", "danger")
        return redirect(url_for("admin.components"))

    form = ComponentForm(obj=comp)
    org = current_user.organization

    form.group_id.choices = [(0, "No Group")]
    for group in ComponentGroup.query.filter_by(organization_id=org.id).all():
        form.group_id.choices.append((group.id, group.name))

    if form.validate_on_submit():
        comp.name = form.name.data
        comp.description = form.description.data
        comp.group_id = form.group_id.data if form.group_id.data != 0 else None
        comp.check_type = form.check_type.data
        comp.check_url = form.check_url.data
        comp.check_method = form.check_method.data
        comp.check_timeout = form.check_timeout.data
        comp.check_interval = form.check_interval.data
        comp.check_expected_status = form.check_expected_status.data
        comp.check_headers = form.check_headers.data
        comp.is_enabled = form.is_enabled.data
        comp.display_order = form.display_order.data or 0
        db.session.commit()
        flash("Component updated successfully", "success")
        return redirect(url_for("admin.components"))

    form.group_id.choices.insert(0, (0, "No Group"))
    return render_template(
        "admin/component_form.html", form=form, action="Edit", component=comp
    )


@admin_bp.route("/components/<int:id>/delete", methods=["POST"])
@login_required
def component_delete(id):
    comp = Component.query.get_or_404(id)
    if comp.organization_id != current_user.organization_id:
        flash("Access denied", "danger")
        return redirect(url_for("admin.components"))

    db.session.delete(comp)
    db.session.commit()
    flash("Component deleted successfully", "success")
    return redirect(url_for("admin.components"))


@admin_bp.route("/components/<int:id>/toggle", methods=["POST"])
@login_required
def component_toggle(id):
    comp = Component.query.get_or_404(id)
    if comp.organization_id != current_user.organization_id:
        return {"error": "Access denied"}, 403

    comp.is_enabled = not comp.is_enabled
    db.session.commit()
    return {"success": True, "is_enabled": comp.is_enabled}


@admin_bp.route("/components/<int:id>/history")
@login_required
def component_history(id):
    comp = Component.query.get_or_404(id)
    if comp.organization_id != current_user.organization_id:
        flash("Access denied", "danger")
        return redirect(url_for("admin.components"))

    hours = request.args.get("hours", 24, type=int)
    history = comp.get_history(hours=hours)

    return render_template(
        "admin/component_history.html", component=comp, history=history, hours=hours
    )


@admin_bp.route("/groups")
@login_required
def groups():
    org = current_user.organization
    groups = (
        ComponentGroup.query.filter_by(organization_id=org.id)
        .order_by(ComponentGroup.display_order)
        .all()
    )

    return render_template("admin/groups.html", groups=groups)


@admin_bp.route("/groups/new", methods=["GET", "POST"])
@login_required
def group_new():
    form = ComponentGroupForm()
    if form.validate_on_submit():
        group = ComponentGroup(
            organization_id=current_user.organization_id,
            name=form.name.data,
            description=form.description.data,
            display_order=form.display_order.data or 0,
        )
        db.session.add(group)
        db.session.commit()
        flash("Group created successfully", "success")
        return redirect(url_for("admin.groups"))

    return render_template("admin/group_form.html", form=form, action="Create")


@admin_bp.route("/groups/<int:id>/edit", methods=["GET", "POST"])
@login_required
def group_edit(id):
    group = ComponentGroup.query.get_or_404(id)
    if group.organization_id != current_user.organization_id:
        flash("Access denied", "danger")
        return redirect(url_for("admin.groups"))

    form = ComponentGroupForm(obj=group)
    if form.validate_on_submit():
        group.name = form.name.data
        group.description = form.description.data
        group.display_order = form.display_order.data or 0
        db.session.commit()
        flash("Group updated successfully", "success")
        return redirect(url_for("admin.groups"))

    return render_template(
        "admin/group_form.html", form=form, action="Edit", group=group
    )


@admin_bp.route("/groups/<int:id>/delete", methods=["POST"])
@login_required
def group_delete(id):
    group = ComponentGroup.query.get_or_404(id)
    if group.organization_id != current_user.organization_id:
        flash("Access denied", "danger")
        return redirect(url_for("admin.groups"))

    if group.components.count() > 0:
        flash("Cannot delete group with components", "warning")
        return redirect(url_for("admin.groups"))

    db.session.delete(group)
    db.session.commit()
    flash("Group deleted successfully", "success")
    return redirect(url_for("admin.groups"))


@admin_bp.route("/incidents")
@login_required
def incidents():
    org = current_user.organization
    incidents = (
        Incident.query.filter_by(organization_id=org.id)
        .order_by(Incident.created_at.desc())
        .all()
    )

    return render_template("admin/incidents.html", incidents=incidents)


@admin_bp.route("/incidents/new", methods=["GET", "POST"])
@login_required
def incident_new():
    form = IncidentForm()
    if form.validate_on_submit():
        incident = Incident(
            organization_id=current_user.organization_id,
            title=form.title.data,
            description=form.description.data,
            severity=form.severity.data,
        )
        db.session.add(incident)
        db.session.commit()

        timeline = IncidentTimeline(
            incident_id=incident.id, status="investigating", message="Incident created"
        )
        db.session.add(timeline)
        db.session.commit()

        flash("Incident created successfully", "success")
        return redirect(url_for("admin.incidents"))

    return render_template("admin/incident_form.html", form=form, action="Create")


@admin_bp.route("/incidents/<int:id>/edit", methods=["GET", "POST"])
@login_required
def incident_edit(id):
    incident = Incident.query.get_or_404(id)
    if incident.organization_id != current_user.organization_id:
        flash("Access denied", "danger")
        return redirect(url_for("admin.incidents"))

    form = IncidentForm(obj=incident)
    if form.validate_on_submit():
        incident.title = form.title.data
        incident.description = form.description.data
        incident.severity = form.severity.data
        db.session.commit()
        flash("Incident updated successfully", "success")
        return redirect(url_for("admin.incidents"))

    return render_template(
        "admin/incident_form.html", form=form, action="Edit", incident=incident
    )


@admin_bp.route("/incidents/<int:id>/delete", methods=["POST"])
@login_required
def incident_delete(id):
    incident = Incident.query.get_or_404(id)
    if incident.organization_id != current_user.organization_id:
        flash("Access denied", "danger")
        return redirect(url_for("admin.incidents"))

    db.session.delete(incident)
    db.session.commit()
    flash("Incident deleted successfully", "success")
    return redirect(url_for("admin.incidents"))


@admin_bp.route("/incidents/<int:id>/view")
@login_required
def incident_detail(id):
    incident = Incident.query.get_or_404(id)
    if incident.organization_id != current_user.organization_id:
        flash("Access denied", "danger")
        return redirect(url_for("admin.incidents"))

    from app.forms import IncidentUpdateForm

    form = IncidentUpdateForm()
    return render_template(
        "admin/incident_detail.html", update_form=form, incident=incident
    )


@admin_bp.route("/incidents/<int:id>/update", methods=["GET", "POST"])
@login_required
def incident_update(id):
    incident = Incident.query.get_or_404(id)
    if incident.organization_id != current_user.organization_id:
        flash("Access denied", "danger")
        return redirect(url_for("admin.incidents"))

    form = IncidentUpdateForm()
    if form.validate_on_submit():
        incident.status = form.status.data
        if form.status.data == "resolved":
            from datetime import datetime

            incident.resolved_at = datetime.utcnow()

        timeline = IncidentTimeline(
            incident_id=incident.id, status=form.status.data, message=form.message.data
        )
        db.session.add(timeline)
        db.session.commit()
        flash("Incident updated successfully", "success")
        return redirect(url_for("admin.incidents"))

    return render_template(
        "admin/incident_detail.html", update_form=form, incident=incident
    )


@admin_bp.route("/incidents/<int:id>/resolve", methods=["POST"])
@login_required
def resolve_incident(id):
    incident = Incident.query.get_or_404(id)
    if incident.organization_id != current_user.organization_id:
        flash("Access denied", "danger")
        return redirect(url_for("admin.incidents"))

    from datetime import datetime

    incident.status = "resolved"
    incident.resolved_at = datetime.utcnow()

    timeline = IncidentTimeline(
        incident_id=incident.id, status="resolved", message="Incident resolved"
    )
    db.session.add(timeline)
    db.session.commit()
    flash("Incident resolved successfully", "success")
    return redirect(url_for("admin.incidents"))


@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    org = current_user.organization
    form = SettingsForm()

    form.organization_name.data = org.name

    branding = org.get_branding()
    form.primary_color.data = branding.get("primary_color", "#2563eb")
    form.custom_css.data = branding.get("custom_css", "")

    if form.validate_on_submit():
        org.name = form.organization_name.data

        branding["primary_color"] = form.primary_color.data
        branding["custom_css"] = form.custom_css.data
        org.set_branding(branding)
        db.session.commit()

        flash("Settings updated successfully", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin/settings.html", form=form)
