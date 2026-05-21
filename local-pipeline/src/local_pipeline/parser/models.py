"""Pydantic models for pipeline YAML parsing."""

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class TriggerConfig(BaseModel):
    type: Literal["cron", "manual", "webhook", "interval"]
    cron: str | None = None
    seconds: int | None = None


class RetryConfig(BaseModel):
    max_attempts: int = 3
    backoff_factor: float = 2.0
    initial_delay: float = 1.0


class TaskConfig(BaseModel):
    id: str
    name: str
    type: Literal["shell", "python", "http"]
    command: str | None = None
    script: str | None = None
    args: list[str] | None = None
    method: str | None = None
    url: str | None = None
    headers: dict[str, str] | None = None
    body: dict[str, Any] | None = None
    env: dict[str, str] | None = None
    output_file: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    timeout: int | None = None
    retry: RetryConfig | None = None


class PipelineDefinition(BaseModel):
    name: str
    description: str | None = None
    version: str = "1.0"
    triggers: list[TriggerConfig] = Field(default_factory=list)
    retry: RetryConfig | None = None
    default_timeout: int = 300
    tasks: list[TaskConfig]

    @field_validator("tasks")
    @classmethod
    def validate_tasks_unique(cls, v: list[TaskConfig]) -> list[TaskConfig]:
        ids = [t.id for t in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Task IDs must be unique")
        for task in v:
            for dep in task.dependencies:
                if dep not in ids:
                    raise ValueError(f"Task {task.id} has unknown dependency: {dep}")
        return v


def interpolate_env_vars(content: str) -> str:
    pattern = re.compile(r"\$\{([^}]+)\}")

    def replacer(match):
        env_var = match.group(1)
        return os.environ.get(env_var, match.group(0))

    import os

    return pattern.sub(replacer, content)


def validate_circular_dependencies(tasks: list[TaskConfig]) -> bool:
    graph: dict[str, set[str]] = {t.id: set(t.dependencies) for t in tasks}
    visited: set[str] = set()
    rec_stack: set[str] = set()

    def has_cycle(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.remove(node)
        return False

    for task_id in graph:
        if task_id not in visited:
            if has_cycle(task_id):
                return True
    return False
