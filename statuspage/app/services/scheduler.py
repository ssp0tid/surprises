from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app import db
from app.models import Component


def init_scheduler(app):
    """Initialize APScheduler with Flask app."""
    scheduler = BackgroundScheduler(max_instances=1, misfire_grace_time=60)
    app.scheduler = scheduler
    scheduler.start()


def schedule_component_checks():
    """Query all enabled components and schedule jobs for each."""
    from flask import current_app

    components = Component.query.filter_by(is_enabled=True).all()
    for component in components:
        _add_or_update_job(component)


def _add_or_update_job(component):
    """Add or update a job for a component."""
    from flask import current_app

    scheduler = current_app.scheduler
    job_id = f"check_{component.id}"

    existing_job = scheduler.get_job(job_id)
    if existing_job:
        scheduler.remove_job(job_id)

    trigger = IntervalTrigger(seconds=component.check_interval)
    scheduler.add_job(
        func=run_health_check, trigger=trigger, job_id=job_id, args=[component.id]
    )


def run_health_check(component_id):
    """Called by scheduler for each component check."""
    from flask import current_app
    from app.services.health_checker import check_component

    with current_app.app_context():
        component = Component.query.get(component_id)
        if component and component.is_enabled:
            check_component(component)


def start_scheduler(app):
    """Called when app starts to initialize and start the scheduler."""
    init_scheduler(app)
    schedule_component_checks()


def stop_scheduler(app):
    """Called when app shuts down to stop the scheduler."""
    if hasattr(app, "scheduler") and app.scheduler:
        app.scheduler.shutdown()


def reschedule_component(component):
    """Update job interval for a component."""
    from flask import current_app

    with current_app.app_context():
        job_id = f"check_{component.id}"
        scheduler = current_app.scheduler

        # Remove old job if exists
        existing_job = scheduler.get_job(job_id)
        if existing_job:
            scheduler.remove_job(job_id)

        # Add new job with updated interval
        if component.is_enabled:
            trigger = IntervalTrigger(seconds=component.check_interval)
            scheduler.add_job(
                func=run_health_check,
                trigger=trigger,
                job_id=job_id,
                args=[component.id],
            )


def remove_component_job(component_id):
    """Remove job from scheduler for a component."""
    from flask import current_app

    with current_app.app_context():
        job_id = f"check_{component_id}"
        scheduler = current_app.scheduler

        existing_job = scheduler.get_job(job_id)
        if existing_job:
            scheduler.remove_job(job_id)
