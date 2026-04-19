from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = BackgroundScheduler()


def schedule_service_checks(app):
    """Initialize scheduler with all active services"""
    with app.app_context():
        from healthdash.models import Service, db

        services = Service.query.filter_by(is_active=True).all()

        for service in services:
            add_job(service)

        if not scheduler.running:
            scheduler.start()


def add_job(service):
    """Add or update a scheduled job for a service"""
    from healthdash.services.checker import perform_health_check

    job_id = f"check_{service.id}"

    # Remove existing job if present
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    # Add new job
    scheduler.add_job(
        func=perform_health_check,
        trigger=IntervalTrigger(seconds=service.check_interval),
        args=[service.id],
        id=job_id,
        replace_existing=True,
    )


def remove_job(service_id):
    """Remove scheduled job for a service"""
    job_id = f"check_{service_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


def shutdown_scheduler():
    """Gracefully shutdown scheduler"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
