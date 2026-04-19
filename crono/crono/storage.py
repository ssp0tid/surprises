"""Data persistence for Crono jobs and history."""

import json
import os
from pathlib import Path
from typing import Optional

from crono.models import CronoData, CronJob, JobHistory


DATA_DIR = Path.home() / ".config" / "crono"
DATA_FILE = DATA_DIR / "data.json"


def ensure_data_dir() -> None:
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True)


def load_data() -> CronoData:
    ensure_data_dir()
    if not DATA_FILE.exists():
        return CronoData()
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            jobs = [CronJob(**j) for j in data.get("jobs", [])]
            history = [JobHistory(**h) for h in data.get("history", [])]
            return CronoData(
                jobs=jobs, history=history, timezone=data.get("timezone", "local")
            )
    except (json.JSONDecodeError, KeyError, TypeError, OSError):
        return CronoData()


def save_data(data: CronoData) -> None:
    ensure_data_dir()
    with open(DATA_FILE, "w") as f:
        json.dump(data.model_dump(mode="json"), f, indent=2, default=str)


def get_all_jobs() -> list[CronJob]:
    return load_data().jobs


def get_job_by_id(job_id: str) -> Optional[CronJob]:
    data = load_data()
    for job in data.jobs:
        if job.id == job_id:
            return job
    return None


def add_job(job: CronJob) -> None:
    data = load_data()
    data.jobs.append(job)
    save_data(data)


def update_job(job: CronJob) -> None:
    data = load_data()
    for i, j in enumerate(data.jobs):
        if j.id == job.id:
            data.jobs[i] = job
            break
    save_data(data)


def delete_job(job_id: str) -> bool:
    data = load_data()
    original_len = len(data.jobs)
    data.jobs = [j for j in data.jobs if j.id != job_id]
    if len(data.jobs) < original_len:
        save_data(data)
        return True
    return False


def add_history(history: JobHistory) -> None:
    data = load_data()
    data.history.append(history)
    data.history = data.history[-1000:]
    save_data(data)


def get_history_for_job(job_id: str, limit: int = 100) -> list[JobHistory]:
    data = load_data()
    job_history = [h for h in data.history if h.job_id == job_id]
    job_history.sort(key=lambda h: h.timestamp, reverse=True)
    return job_history[:limit]


def get_all_history(limit: int = 100) -> list[JobHistory]:
    data = load_data()
    data.history.sort(key=lambda h: h.timestamp, reverse=True)
    return data.history[:limit]
