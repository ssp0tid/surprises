"""Job CRUD operations and business logic."""

from datetime import datetime
from typing import Optional

from crono import cron_parser
from crono.models import CronJob
from crono import storage
from crono import history


class JobManager:
    @staticmethod
    def create_job(
        name: str,
        command: str,
        cron_expression: str,
        description: str = "",
        enabled: bool = True,
    ) -> tuple[Optional[CronJob], Optional[str]]:
        valid, error = cron_parser.validate(cron_expression)
        if not valid:
            return None, error

        existing = storage.get_all_jobs()
        if any(j.name == name for j in existing):
            return None, f"Job '{name}' already exists"

        next_runs = cron_parser.get_next_run(cron_expression, 1)
        job = CronJob(
            name=name,
            command=command,
            cron_expression=cron_expression,
            description=description,
            enabled=enabled,
            next_run=next_runs[0] if next_runs else None,
        )
        storage.add_job(job)
        return job, None

    @staticmethod
    def update_job(
        job_id: str,
        name: Optional[str] = None,
        command: Optional[str] = None,
        cron_expression: Optional[str] = None,
        description: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> tuple[Optional[CronJob], Optional[str]]:
        job = storage.get_job_by_id(job_id)
        if not job:
            return None, "Job not found"

        if name is not None:
            existing = storage.get_all_jobs()
            if any(j.name == name and j.id != job_id for j in existing):
                return None, f"Job '{name}' already exists"
            job.name = name

        if command is not None:
            job.command = command

        if cron_expression is not None:
            valid, error = cron_parser.validate(cron_expression)
            if not valid:
                return None, error
            job.cron_expression = cron_expression
            next_runs = cron_parser.get_next_run(cron_expression, 1)
            job.next_run = next_runs[0] if next_runs else None

        if description is not None:
            job.description = description

        if enabled is not None:
            job.enabled = enabled

        job.updated_at = datetime.now()
        storage.update_job(job)
        return job, None

    @staticmethod
    def delete_job(job_id: str) -> bool:
        return storage.delete_job(job_id)

    @staticmethod
    def get_job(job_id: str) -> Optional[CronJob]:
        return storage.get_job_by_id(job_id)

    @staticmethod
    def get_all_jobs() -> list[CronJob]:
        return storage.get_all_jobs()

    @staticmethod
    def toggle_job(job_id: str) -> tuple[Optional[CronJob], Optional[str]]:
        job = storage.get_job_by_id(job_id)
        if not job:
            return None, "Job not found"
        job.enabled = not job.enabled
        job.updated_at = datetime.now()
        storage.update_job(job)
        return job, None

    @staticmethod
    def run_job(job_id: str) -> tuple[Optional[CronJob], Optional[str]]:
        job = storage.get_job_by_id(job_id)
        if not job:
            return None, "Job not found"
        record = history.run_and_log(job)
        if record.status == "failed":
            return None, record.error
        return job, None
