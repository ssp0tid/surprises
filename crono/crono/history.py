"""Job execution history logging."""

import subprocess
import time
from datetime import datetime
from typing import Optional

from crono.models import CronJob, JobHistory
from crono import storage


def run_and_log(job: CronJob) -> JobHistory:
    start_time = time.time()
    record = JobHistory(
        job_id=job.id,
        timestamp=datetime.now(),
        status="running",
    )
    try:
        result = subprocess.run(
            job.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
        )
        record.duration = time.time() - start_time
        if result.returncode == 0:
            record.status = "success"
            record.output = result.stdout[:5000] if result.stdout else ""
        else:
            record.status = "failed"
            record.output = result.stdout[:2500] if result.stdout else ""
            record.error = (
                result.stderr[:2500] if result.stderr else "Non-zero exit code"
            )
    except subprocess.TimeoutExpired:
        record.status = "timeout"
        record.duration = 300.0
        record.error = "Job timed out after 300 seconds"
    except Exception as e:
        record.status = "failed"
        record.duration = time.time() - start_time
        record.error = str(e)[:500]

    storage.add_history(record)
    return record


def get_history_for_job(job_id: str, limit: int = 100) -> list[JobHistory]:
    return storage.get_history_for_job(job_id, limit)


def get_all_history(limit: int = 100) -> list[JobHistory]:
    return storage.get_all_history(limit)


def format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
