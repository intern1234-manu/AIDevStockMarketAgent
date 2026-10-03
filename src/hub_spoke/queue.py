from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Iterable, List, Optional


@dataclass
class QueueTask:
    task_id: str
    title: str
    description: str
    priority: str = "normal"
    dependencies: List[str] = field(default_factory=list)
    workers: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class TaskQueue:
    """Simple in-memory task queue for workflow execution."""

    def __init__(self) -> None:
        self._queue: Deque[QueueTask] = deque()
        self._completed: List[QueueTask] = []

    def enqueue(self, task: QueueTask) -> None:
        self._queue.append(task)

    def enqueue_many(self, tasks: Iterable[QueueTask]) -> None:
        for task in tasks:
            self.enqueue(task)

    def dequeue(self) -> Optional[QueueTask]:
        if not self._queue:
            return None
        task = self._queue.popleft()
        self._completed.append(task)
        return task

    def complete(self, task_id: str) -> Optional[QueueTask]:
        for task in list(self._queue):
            if task.task_id == task_id:
                self._queue.remove(task)
                self._completed.append(task)
                return task
        return None

    def peek(self) -> Optional[QueueTask]:
        if not self._queue:
            return None
        return self._queue[0]

    @property
    def tasks(self) -> List[QueueTask]:
        return list(self._queue)

    def __len__(self) -> int:
        return len(self._queue)

    def __bool__(self) -> bool:
        return bool(self._queue)

    @property
    def completed(self) -> List[QueueTask]:
        return list(self._completed)
