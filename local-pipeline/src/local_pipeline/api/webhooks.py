"""Webhook handlers for external triggers."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import Pipeline
from ..engine.executor import PipelineExecutor
from ..parser.loader import parse_pipeline
from .schemas import WebhookPayload, RunResponse

router = APIRouter(prefix="/api/v1/webhooks")


@router.post("/{pipeline_id}", response_model=RunResponse)
async def trigger_webhook(
    pipeline_id: str,
    payload: WebhookPayload,
    x_webhook_signature: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
):
    pipeline = await session.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    try:
        pipeline_def = parse_pipeline(pipeline.yaml_content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid pipeline: {e}")

    has_webhook_trigger = any(t.type == "webhook" for t in pipeline_def.triggers)
    if not has_webhook_trigger:
        raise HTTPException(status_code=400, detail="Pipeline does not support webhook triggers")

    executor = PipelineExecutor(pipeline, pipeline_def)
    run = await executor.execute(
        triggered_by="webhook",
        trigger_source=payload.source or payload.event,
    )

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
