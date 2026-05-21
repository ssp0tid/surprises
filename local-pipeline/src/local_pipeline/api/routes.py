"""REST API routes for pipeline management."""

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_session
from ..models import Pipeline, Run, Task, RunStatus, TaskStatus
from ..engine.executor import PipelineExecutor
from ..parser.loader import parse_pipeline
from .schemas import (
    PipelineCreate,
    PipelineUpdate,
    PipelineResponse,
    RunResponse,
    TaskResponse,
    PaginatedResponse,
    HealthResponse,
    MetricsResponse,
)

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.utcnow(),
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(session: AsyncSession = Depends(get_session)):
    pipeline_count = await session.scalar(select(func.count(Pipeline.id)))
    run_count = await session.scalar(select(func.count(Run.id)))
    running_count = await session.scalar(
        select(func.count(Run.id)).where(Run.status == RunStatus.RUNNING.value)
    )

    success_count = await session.scalar(
        select(func.count(Run.id)).where(Run.status == RunStatus.SUCCESS.value)
    )
    success_rate = (success_count / run_count * 100) if run_count else 0.0

    return MetricsResponse(
        total_pipelines=pipeline_count or 0,
        total_runs=run_count or 0,
        running_runs=running_count or 0,
        success_rate=round(success_rate, 2),
    )


@router.get("/pipelines", response_model=list[PipelineResponse])
async def list_pipelines(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Pipeline).offset(skip).limit(limit))
    pipelines = result.scalars().all()
    return [
        PipelineResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            version=p.version,
            yaml_path=p.yaml_path,
            is_active=p.is_active,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in pipelines
    ]


@router.post("/pipelines", response_model=PipelineResponse)
async def create_pipeline(
    data: PipelineCreate,
    session: AsyncSession = Depends(get_session),
):
    try:
        pipeline_def = parse_pipeline(data.yaml_content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    existing = await session.scalar(select(Pipeline).where(Pipeline.name == data.name))
    if existing:
        raise HTTPException(status_code=400, detail="Pipeline already exists")

    pipeline = Pipeline(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        version=pipeline_def.version,
        yaml_path="",
        yaml_content=data.yaml_content,
    )
    session.add(pipeline)
    await session.commit()
    await session.refresh(pipeline)

    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        version=pipeline.version,
        yaml_path=pipeline.yaml_path,
        is_active=pipeline.is_active,
        created_at=pipeline.created_at,
        updated_at=pipeline.updated_at,
    )


@router.get("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
):
    pipeline = await session.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        version=pipeline.version,
        yaml_path=pipeline.yaml_path,
        is_active=pipeline.is_active,
        created_at=pipeline.created_at,
        updated_at=pipeline.updated_at,
    )


@router.put("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: str,
    data: PipelineUpdate,
    session: AsyncSession = Depends(get_session),
):
    pipeline = await session.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if data.name is not None:
        pipeline.name = data.name
    if data.description is not None:
        pipeline.description = data.description
    if data.yaml_content is not None:
        try:
            pipeline_def = parse_pipeline(data.yaml_content)
            pipeline.version = pipeline_def.version
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        pipeline.yaml_content = data.yaml_content
    if data.is_active is not None:
        pipeline.is_active = data.is_active

    await session.commit()
    await session.refresh(pipeline)

    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        version=pipeline.version,
        yaml_path=pipeline.yaml_path,
        is_active=pipeline.is_active,
        created_at=pipeline.created_at,
        updated_at=pipeline.updated_at,
    )


@router.delete("/pipelines/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
):
    pipeline = await session.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    await session.delete(pipeline)
    await session.commit()
    return {"message": "Pipeline deleted"}


@router.post("/pipelines/{pipeline_id}/trigger", response_model=RunResponse)
async def trigger_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
):
    pipeline = await session.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    try:
        pipeline_def = parse_pipeline(pipeline.yaml_content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid pipeline: {e}")

    executor = PipelineExecutor(pipeline, pipeline_def)
    run = await executor.execute(triggered_by="manual")

    return RunResponse(
        id=run.id,
        pipeline_id=run.pipeline_id,
        run_number=run.run_number,
        status=run.status,
        triggered_by=run.triggered_by,
        trigger_source=run.trigger_source,
        started_at=run.started_at,
        finished_at=run.finished_at,
        duration_ms=run.duration_ms,
        created_at=run.created_at,
    )


@router.post("/pipelines/{pipeline_id}/cancel")
async def cancel_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Run)
        .where(Run.pipeline_id == pipeline_id)
        .where(Run.status == RunStatus.RUNNING.value)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="No running pipeline found")

    run.status = RunStatus.CANCELLED.value
    await session.commit()
    return {"message": "Pipeline cancelled"}


@router.get("/runs", response_model=PaginatedResponse)
async def list_runs(
    pipeline_id: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_session),
):
    query = select(Run)
    if pipeline_id:
        query = query.where(Run.pipeline_id == pipeline_id)
    if status:
        query = query.where(Run.status == status)

    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query.order_by(Run.created_at.desc()))
    runs = result.scalars().all()

    return PaginatedResponse(
        items=[
            RunResponse(
                id=r.id,
                pipeline_id=r.pipeline_id,
                run_number=r.run_number,
                status=r.status,
                triggered_by=r.triggered_by,
                trigger_source=r.trigger_source,
                started_at=r.started_at,
                finished_at=r.finished_at,
                duration_ms=r.duration_ms,
                created_at=r.created_at,
            )
            for r in runs
        ],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
):
    run = await session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return RunResponse(
        id=run.id,
        pipeline_id=run.pipeline_id,
        run_number=run.run_number,
        status=run.status,
        triggered_by=run.triggered_by,
        trigger_source=run.trigger_source,
        started_at=run.started_at,
        finished_at=run.finished_at,
        duration_ms=run.duration_ms,
        created_at=run.created_at,
    )


@router.get("/runs/{run_id}/tasks", response_model=list[TaskResponse])
async def get_run_tasks(
    run_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Task).where(Task.run_id == run_id).order_by(Task.created_at)
    )
    tasks = result.scalars().all()

    return [
        TaskResponse(
            id=t.id,
            run_id=t.run_id,
            pipeline_task_id=t.pipeline_task_id,
            name=t.name,
            task_type=t.task_type,
            status=t.status,
            output=t.output,
            error=t.error,
            started_at=t.started_at,
            finished_at=t.finished_at,
            duration_ms=t.duration_ms,
            attempt=t.attempt,
        )
        for t in tasks
    ]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
):
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse(
        id=task.id,
        run_id=task.run_id,
        pipeline_task_id=task.pipeline_task_id,
        name=task.name,
        task_type=task.task_type,
        status=task.status,
        output=task.output,
        error=task.error,
        started_at=task.started_at,
        finished_at=task.finished_at,
        duration_ms=task.duration_ms,
        attempt=task.attempt,
    )


@router.post("/tasks/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
):
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatus.FAILED.value:
        raise HTTPException(status_code=400, detail="Only failed tasks can be retried")

    task.status = TaskStatus.PENDING.value
    task.attempt = 1
    await session.commit()

    return TaskResponse(
        id=task.id,
        run_id=task.run_id,
        pipeline_task_id=task.pipeline_task_id,
        name=task.name,
        task_type=task.task_type,
        status=task.status,
        output=task.output,
        error=task.error,
        started_at=task.started_at,
        finished_at=task.finished_at,
        duration_ms=task.duration_ms,
        attempt=task.attempt,
    )
