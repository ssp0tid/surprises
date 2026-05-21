"""Thread pool workers for task execution."""

import asyncio
import os
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from pathlib import Path
from typing import Any, Callable, Coroutine

import httpx

from ..parser.models import TaskConfig
from .retry import RetryPolicy


class TaskWorker:
    def __init__(self, task: TaskConfig, timeout: int = 300):
        self.task = task
        self.timeout = task.timeout or timeout
        self._result: str | None = None
        self._error: str | None = None

    async def execute(self) -> tuple[str, str]:
        if self.task.type == "shell":
            return await self._execute_shell()
        elif self.task.type == "python":
            return await self._execute_python()
        elif self.task.type == "http":
            return await self._execute_http()
        raise ValueError(f"Unknown task type: {self.task.type}")

    async def _execute_shell(self) -> tuple[str, str]:
        cmd = self.task.command
        env = os.environ.copy()
        if self.task.env:
            env.update(self.task.env)

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                raise TimeoutError(f"Task timed out after {self.timeout}s")

            result = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""

            if self.task.output_file and result:
                Path(self.task.output_file).write_text(result)

            return result, error
        except Exception as e:
            return "", str(e)

    async def _execute_python(self) -> tuple[str, str]:
        script = self.task.script
        args = self.task.args or []

        cmd = ["python", script] + args
        env = os.environ.copy()
        if self.task.env:
            env.update(self.task.env)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                raise TimeoutError(f"Task timed out after {self.timeout}s")

            result = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""
            return result, error
        except Exception as e:
            return "", str(e)

    async def _execute_http(self) -> tuple[str, str]:
        method = self.task.method or "GET"
        url = self.task.url
        headers = self.task.headers or {}
        body = self.task.body

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    json=body,
                    timeout=self.timeout,
                )
            return response.text, ""
        except Exception as e:
            return "", str(e)


class WorkerPool:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running: set[str] = set()
        self._lock = threading.Lock()

    def submit(self, coro: Coroutine, task_id: str) -> Future:
        with self._lock:
            self._running.add(task_id)

        def done(fut):
            with self._lock:
                self._running.discard(task_id)

        fut = self.executor.submit(asyncio.run, coro)
        fut.add_done_callback(done)
        return fut

    def is_running(self, task_id: str) -> bool:
        with self._lock:
            return task_id in self._running

    def shutdown(self, wait: bool = True):
        self.executor.shutdown(wait=wait)
