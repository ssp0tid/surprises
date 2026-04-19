"""Data models for Crono."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class CronJob(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    command: str
    cron_expression: str
    description: str = ""
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


class JobHistory(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    job_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    status: str = "pending"
    duration: float = 0.0
    output: str = ""
    error: Optional[str] = None


class CronoData(BaseModel):
    jobs: list[CronJob] = Field(default_factory=list)
    history: list[JobHistory] = Field(default_factory=list)
    timezone: str = "local"
