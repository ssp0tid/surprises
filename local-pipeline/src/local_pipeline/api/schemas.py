"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PipelineCreate(BaseModel):
    name: str
    description: str | None = None
    yaml_content: str


class PipelineUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    yaml_content: str | None = None
    is_active: bool | None = None


class PipelineResponse(BaseModel):
    id: str
    name: str
    description: str | None
    version: str
    yaml_path: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RunCreate(BaseModel):
    pass


class RunResponse(BaseModel):
    id: str
    pipeline_id: str
    run_number: int
    status: str
    triggered_by: str
    trigger_source: str | None
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    created_at: datetime


class TaskResponse(BaseModel):
    id: str
    run_id: str
    pipeline_task_id: str
    name: str
    task_type: str
    status: str
    output: str | None
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    attempt: int


class TriggerRequest(BaseModel):
    source: str | None = None


class WebhookPayload(BaseModel):
    event: str | None = None
    source: str | None = None
    payload: dict[str, Any] | None = None
    timestamp: datetime | None = None
    signature: str | None = None


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int = 1
    page_size: int = 20


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


class MetricsResponse(BaseModel):
    total_pipelines: int
    total_runs: int
    running_runs: int
    success_rate: float
