"""DAG scheduler with topological sort."""

from collections import defaultdict, deque
from typing import Any

from ..parser.models import TaskConfig


class DAGScheduler:
    def __init__(self, tasks: list[TaskConfig]):
        self.tasks = {t.id: t for t in tasks}
        self.graph: dict[str, set[str]] = {t.id: set(t.dependencies) for t in tasks}
        self.in_degree: dict[str, int] = {t.id: len(t.dependencies) for t in tasks}

    def topological_sort(self) -> list[TaskConfig]:
        queue = deque([tid for tid, deg in self.in_degree.items() if deg == 0])
        result = []

        while queue:
            task_id = queue.popleft()
            result.append(self.tasks[task_id])

            for dependent in self.graph.get(task_id, []):
                self.in_degree[dependent] -= 1
                if self.in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(result) != len(self.tasks):
            raise ValueError("Circular dependency detected in pipeline")

        return result

    def get_ready_tasks(self, completed: set[str], running: set[str]) -> list[TaskConfig]:
        ready = []
        for task_id, deps in self.graph.items():
            if task_id not in completed and task_id not in running:
                if deps.issubset(completed):
                    ready.append(self.tasks[task_id])
        return ready

    def get_execution_levels(self) -> list[list[TaskConfig]]:
        levels = []
        remaining = set(self.tasks.keys())
        completed = set()

        while remaining:
            level = []
            for task_id in list(remaining):
                deps = self.graph.get(task_id, set())
                if deps.issubset(completed):
                    level.append(self.tasks[task_id])

            if not level:
                raise ValueError("Circular dependency detected")

            levels.append(level)
            for task in level:
                remaining.remove(task.id)
                completed.add(task.id)

        return levels
