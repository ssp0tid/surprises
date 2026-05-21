"""Main execution engine for pipeline runs."""

import asyncio
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import async_session_factory
from ..models import Pipeline, Run, Task, TaskDependency, TaskStatus, RunStatus
from ..parser.models import PipelineDefinition, TaskConfig, RetryConfig
from .scheduler import DAGScheduler
from .workers import TaskWorker, WorkerPool
from .retry import RetryPolicy
from ..config import config


class PipelineExecutor:
    def __init__(self, pipeline: Pipeline, definition: PipelineDefinition):
        self.pipeline = pipeline
        self.definition = definition
        self.scheduler = DAGScheduler(definition.tasks)
        self.worker_pool = WorkerPool(max_workers=config.execution.max_parallel_tasks)
        self._run: Run | None = None
        self._tasks: dict[str, Task] = {}
        self._cancelled = False

    async def execute(self, triggered_by: str, trigger_source: str | None = None) -> Run:
        async with async_session_factory() as session:
            run = await self._create_run(session, triggered_by, trigger_source)
            self._run = run
            await session.commit()

            try:
                await self._execute_tasks(session)
                await self._finalize_run(session)
            except Exception as e:
                run.status = RunStatus.FAILED.value
                run.error = str(e)
                await session.commit()
                raise

            await session.refresh(run)
            return run

    async def _create_run(
        self, session: AsyncSession, triggered_by: str, trigger_source: str | None
    ) -> Run:
        result = await session.execute(
            select(Run)
            .where(Run.pipeline_id == self.pipeline.id)
            .order_by(Run.run_number.desc())
            .limit(1)
        )
        last_run = result.scalar_one_or_none()
        run_number = (last_run.run_number + 1) if last_run else 1

        run = Run(
            id=str(uuid.uuid4()),
            pipeline_id=self.pipeline.id,
            run_number=run_number,
            status=RunStatus.RUNNING.value,
            triggered_by=triggered_by,
            trigger_source=trigger_source,
            started_at=datetime.utcnow(),
        )
        session.add(run)
        await session.flush()

        for task_config in self.definition.tasks:
            task = Task(
                id=str(uuid.uuid4()),
                run_id=run.id,
                pipeline_task_id=task_config.id,
                name=task_config.name,
                task_type=task_config.type,
                status=TaskStatus.PENDING.value,
            )
            session.add(task)
            self._tasks[task_config.id] = task

        for task_config in self.definition.tasks:
            task = self._tasks[task_config.id]
            for dep_ref in task_config.dependencies:
                dep_task = self._tasks[dep_ref]
                dependency = TaskDependency(
                    task_id=task.id,
                    depends_on_task_id=dep_task.id,
                    depends_on_task_ref=dep_ref,
                )
                session.add(dependency)

        await session.flush()
        return run

    async def _execute_tasks(self, session: AsyncSession):
        levels = self.scheduler.get_execution_levels()

        for level_idx, level in enumerate(levels):
            if self._cancelled:
                for task_config in level:
                    task = self._tasks[task_config.id]
                    task.status = TaskStatus.SKIPPED.value
                break

            tasks_to_run = []
            for task_config in level:
                task = self._tasks[task_config.id]
                deps = [self._tasks[dep].status for dep in task_config.dependencies]
                if all(d == TaskStatus.SUCCESS.value for d in deps):
                    tasks_to_run.append((task_config, task))

            if not tasks_to_run:
                continue

            futures = []
            for task_config, task in tasks_to_run:
                future = self.worker_pool.submit(
                    self._execute_task(session, task_config, task),
                    task_config.id,
                )
                futures.append((task_config, task, future))

            for task_config, task, future in futures:
                try:
                    await asyncio.wrap_future(future)
                except Exception as e:
                    task.status = TaskStatus.FAILED.value
                    task.error = str(e)

            await session.commit()

    async def _execute_task(self, session: AsyncSession, task_config: TaskConfig, task: Task):
        retry_policy = RetryPolicy.from_config(task_config.retry or self.definition.retry)
        max_attempts = retry_policy.max_attempts

        for attempt in range(1, max_attempts + 1):
            if self._cancelled:
                task.status = TaskStatus.SKIPPED.value
                return

            task.status = TaskStatus.RUNNING.value
            task.attempt = attempt
            task.started_at = datetime.utcnow()
            await session.commit()

            worker = TaskWorker(task_config, self.definition.default_timeout)

            try:
                output, error = await worker.execute()
                task.output = output
                task.error = error

                if error and attempt < max_attempts:
                    task.status = TaskStatus.RETRYING.value
                    await session.commit()
                    delay = retry_policy.get_delay(attempt)
                    await asyncio.sleep(delay)
                    continue

                if error:
                    task.status = TaskStatus.FAILED.value
                else:
                    task.status = TaskStatus.SUCCESS.value

                task.finished_at = datetime.utcnow()
                if task.started_at:
                    task.duration_ms = int(
                        (task.finished_at - task.started_at).total_seconds() * 1000
                    )
                await session.commit()
                return

            except Exception as e:
                task.error = str(e)
                if attempt < max_attempts:
                    task.status = TaskStatus.RETRYING.value
                    await session.commit()
                    delay = retry_policy.get_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    task.status = TaskStatus.FAILED.value
                    task.finished_at = datetime.utcnow()
                    await session.commit()

    async def _finalize_run(self, session: AsyncSession):
        task_statuses = [t.status for t in self._tasks.values()]

        if self._cancelled:
            self._run.status = RunStatus.CANCELLED.value
        elif all(s == TaskStatus.SUCCESS.value for s in task_statuses):
            self._run.status = RunStatus.SUCCESS.value
        elif any(s == TaskStatus.FAILED.value for s in task_statuses):
            self._run.status = RunStatus.FAILED.value
        else:
            self._run.status = RunStatus.SUCCESS.value

        self._run.finished_at = datetime.utcnow()
        if self._run.started_at:
            self._run.duration_ms = int(
                (self._run.finished_at - self._run.started_at).total_seconds() * 1000
            )
        await session.commit()

    def cancel(self):
        self._cancelled = True
        self.worker_pool.shutdown(wait=False)
