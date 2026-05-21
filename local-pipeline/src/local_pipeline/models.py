"""Database models for local-pipeline."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    yaml_path: Mapped[str] = mapped_column(String(500), nullable=False)
    yaml_content: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    runs: Mapped[list["Run"]] = relationship(
        back_populates="pipeline", cascade="all, delete-orphan"
    )


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (
        Index("idx_runs_pipeline", "pipeline_id"),
        Index("idx_runs_status", "status"),
        Index("idx_runs_created", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    pipeline_id: Mapped[str] = mapped_column(String(100), nullable=False)
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RunStatus.PENDING.value,
    )
    triggered_by: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    pipeline: Mapped["Pipeline"] = relationship(back_populates="runs")
    tasks: Mapped[list["Task"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("idx_tasks_run", "run_id"),
        Index("idx_tasks_status", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(String(100), nullable=False)
    pipeline_task_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TaskStatus.PENDING.value,
    )
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    run: Mapped["Run"] = relationship(back_populates="tasks")
    dependencies: Mapped[list["TaskDependency"]] = relationship(
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    logs: Mapped[list["ExecutionLog"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )


class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    __table_args__ = (
        Index("idx_deps_task", "task_id"),
        Index("idx_deps_on", "depends_on_task_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(100), nullable=False)
    depends_on_task_id: Mapped[str] = mapped_column(String(100), nullable=False)
    depends_on_task_ref: Mapped[str] = mapped_column(String(100), nullable=False)

    task: Mapped["Task"] = relationship(foreign_keys=[task_id], back_populates="dependencies")


class ExecutionLog(Base):
    __tablename__ = "execution_logs"
    __table_args__ = (
        Index("idx_logs_task", "task_id"),
        Index("idx_logs_run", "run_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    run_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["Task"] = relationship(back_populates="logs")
