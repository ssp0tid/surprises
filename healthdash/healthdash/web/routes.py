from flask import render_template, redirect, url_for, flash, request
from healthdash.web import web_bp
from healthdash.models import Service, HealthCheck, db
from healthdash.services.scheduler import add_job, remove_job
from healthdash.services.checker import perform_health_check


@web_bp.route("/")
def index():
    services = Service.query.order_by(Service.created_at.desc()).all()
    return render_template("index.html", services=services)


@web_bp.route("/add", methods=["GET"])
def add_service_form():
    return render_template("add_service.html")


@web_bp.route("/add", methods=["POST"])
def add_service():
    name = request.form.get("name", "").strip()
    url = request.form.get("url", "").strip()
    method = request.form.get("method", "GET").upper()
    expected_status = request.form.get("expected_status", 200, type=int)
    check_interval = request.form.get("check_interval", 60, type=int)
    timeout = request.form.get("timeout", 10, type=int)

    errors = []
    if not name:
        errors.append("Name is required")
    if not url:
        errors.append("URL is required")
    if not url.startswith(("http://", "https://")):
        errors.append("URL must start with http:// or https://")
    if check_interval < 10 or check_interval > 3600:
        errors.append("Check interval must be between 10 and 3600 seconds")
    if timeout < 1 or timeout > 60:
        errors.append("Timeout must be between 1 and 60 seconds")
    if method not in ("GET", "POST", "HEAD"):
        errors.append("Method must be GET, POST, or HEAD")

    if errors:
        for error in errors:
            flash(error, "danger")
        return redirect(url_for("web.add_service_form"))

    service = Service(
        name=name,
        url=url,
        method=method,
        expected_status=expected_status,
        check_interval=check_interval,
        timeout=timeout,
        is_active=True,
    )
    db.session.add(service)
    db.session.commit()
    add_job(service)

    flash(f"Service '{name}' created successfully", "success")
    return redirect(url_for("web.index"))


@web_bp.route("/service/<int:service_id>")
def service_detail(service_id):
    service = Service.query.get_or_404(service_id)
    checks = service.checks.order_by(HealthCheck.timestamp.desc()).limit(20).all()
    return render_template("service_detail.html", service=service, checks=checks)


@web_bp.route("/service/<int:service_id>/edit", methods=["GET"])
def edit_service_form(service_id):
    service = Service.query.get_or_404(service_id)
    return render_template("edit_service.html", service=service)


@web_bp.route("/service/<int:service_id>/edit", methods=["POST"])
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)

    name = request.form.get("name", "").strip()
    url = request.form.get("url", "").strip()
    method = request.form.get("method", "GET").upper()
    expected_status = request.form.get("expected_status", 200, type=int)
    check_interval = request.form.get("check_interval", 60, type=int)
    timeout = request.form.get("timeout", 10, type=int)

    errors = []
    if not name:
        errors.append("Name is required")
    if not url:
        errors.append("URL is required")
    if not url.startswith(("http://", "https://")):
        errors.append("URL must start with http:// or https://")
    if check_interval < 10 or check_interval > 3600:
        errors.append("Check interval must be between 10 and 3600 seconds")
    if timeout < 1 or timeout > 60:
        errors.append("Timeout must be between 1 and 60 seconds")
    if method not in ("GET", "POST", "HEAD"):
        errors.append("Method must be GET, POST, or HEAD")

    if errors:
        for error in errors:
            flash(error, "danger")
        return redirect(url_for("web.edit_service_form", service_id=service_id))

    service.name = name
    service.url = url
    service.method = method
    service.expected_status = expected_status
    service.check_interval = check_interval
    service.timeout = timeout

    db.session.commit()

    if service.is_active:
        add_job(service)

    flash(f"Service '{name}' updated successfully", "success")
    return redirect(url_for("web.service_detail", service_id=service_id))


@web_bp.route("/service/<int:service_id>/delete", methods=["POST"])
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    remove_job(service_id)
    db.session.delete(service)
    db.session.commit()

    flash(f"Service '{service.name}' deleted successfully", "success")
    return redirect(url_for("web.index"))


@web_bp.route("/service/<int:service_id>/toggle", methods=["POST"])
def toggle_service(service_id):
    service = Service.query.get_or_404(service_id)
    service.is_active = not service.is_active
    db.session.commit()

    if service.is_active:
        add_job(service)
    else:
        remove_job(service_id)

    status = "activated" if service.is_active else "deactivated"
    flash(f"Service '{service.name}' {status}", "success")
    return redirect(url_for("web.index"))


@web_bp.route("/service/<int:service_id>/check", methods=["POST"])
def trigger_check(service_id):
    service = Service.query.get_or_404(service_id)
    check = perform_health_check(service_id)

    if check:
        if check.is_up:
            flash(
                f"Check passed for '{service.name}' ({check.response_time}ms)",
                "success",
            )
        else:
            flash(f"Check failed for '{service.name}': {check.error_message}", "danger")
    else:
        flash(f"Could not perform check for inactive service", "warning")

    return redirect(
        request.referrer or url_for("web.service_detail", service_id=service_id)
    )
