from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence

from .driver_agent import StockPlannerDriver
from .models import AgentTask
from .queue import QueueTask, TaskQueue
from .task_scheduler import PRIORITY_ORDER, TaskScheduler


@dataclass
class WorkflowResult:
    task_id: str
    title: str
    assigned_workers: List[str]
    status: str
    output: Dict[str, object] = field(default_factory=dict)


class WorkflowEngine:
    """Workflow engine that processes only tasks whose prerequisites are already satisfied."""

    def __init__(self, driver: Optional[StockPlannerDriver] = None) -> None:
        self.driver = driver or StockPlannerDriver()
        self.queue = TaskQueue()
        self.history: List[WorkflowResult] = []
        self.completed_ids: set[str] = set()

    def enqueue(self, task: AgentTask) -> None:
        queue_task = QueueTask(
            task_id=task.task_id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            dependencies=[],
            workers=self.driver.classify_task(task),
            metadata={"context": task.context, "tags": task.tags},
        )
        self.queue.enqueue(queue_task)

    def submit(self, task: AgentTask, dependencies: Optional[Sequence[str]] = None) -> None:
        queue_task = QueueTask(
            task_id=task.task_id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            dependencies=list(dependencies or []),
            workers=self.driver.classify_task(task),
            metadata={"context": task.context, "tags": task.tags},
        )
        self.queue.enqueue(queue_task)

    def _ready_tasks(self) -> List[QueueTask]:
        ready: List[QueueTask] = []
        for task in self.queue.tasks:
            if all(dep in self.completed_ids for dep in task.dependencies):
                ready.append(task)
        return ready

    def _resolve_next_task(self) -> Optional[QueueTask]:
        ready_tasks = self._ready_tasks()
        if not ready_tasks:
            return None
        return max(
            ready_tasks,
            key=lambda task: (PRIORITY_ORDER.get(task.priority.lower(), 0), task.title.lower()),
        )

    def run(self, mode: str = "sequential") -> List[WorkflowResult]:
        results: List[WorkflowResult] = []

        while self.queue:
            next_task = self._resolve_next_task()
            if next_task is None:
                pending = self.queue.tasks
                blockers = {
                    task.task_id: [dep for dep in task.dependencies if dep not in self.completed_ids]
                    for task in pending
                }
                raise RuntimeError(f"No runnable tasks. Remaining blockers: {blockers}")

            converted = AgentTask(
                task_id=next_task.task_id,
                title=next_task.title,
                description=next_task.description,
                priority=next_task.priority,
                context=next_task.metadata.get("context", {}),
                tags=next_task.metadata.get("tags", []),
            )

            if mode == "parallel":
                output = self.driver.execute_parallel(converted, next_task.workers)
            else:
                output = self.driver.execute(converted)

            results.append(
                WorkflowResult(
                    task_id=converted.task_id,
                    title=converted.title,
                    assigned_workers=next_task.workers,
                    status="completed",
                    output=output,
                )
            )
            self.queue.complete(next_task.task_id)
            self.completed_ids.add(next_task.task_id)

        self.history.extend(results)
        return results

    def run_many(self, tasks: Iterable[AgentTask], mode: str = "sequential") -> List[WorkflowResult]:
        for task in tasks:
            self.submit(task)
        return self.run(mode=mode)
