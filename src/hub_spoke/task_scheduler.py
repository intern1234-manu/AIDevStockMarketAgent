from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .models import AgentTask

PRIORITY_ORDER = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "normal": 2,
    "low": 1,
}


@dataclass
class ScheduledTask:
    task: AgentTask
    priority: str
    mode: str


class TaskScheduler:
    """Reusable scheduler that decides priority and run style for tasks."""

    @staticmethod
    def normalize_priority(priority: str | None) -> str:
        value = (priority or "normal").strip().lower()
        if value not in PRIORITY_ORDER:
            return "normal"
        return value

    @staticmethod
    def decide_mode(worker_names: Sequence[str], force: str | None = None, task: AgentTask | None = None) -> str:
        if force:
            return force.lower()
        if task is not None:
            text = f"{task.title} {task.description} {' '.join(task.tags)}".lower()
            if any(keyword in text for keyword in ["execution", "risk", "broker", "trade", "order", "live", "veto"]):
                return "sequential"
            if any(keyword in text for keyword in ["history", "analysis", "signal", "technical", "fundamental", "model", "paper"]):
                return "parallel"
        if len(set(worker_names)) > 1:
            return "parallel"
        return "sequential"

    @staticmethod
    def schedule(tasks: Iterable[AgentTask], force_mode: str | None = None) -> List[ScheduledTask]:
        scheduled: List[ScheduledTask] = []
        for task in tasks:
            priority = TaskScheduler.normalize_priority(task.priority)
            mode = force_mode or TaskScheduler.decide_mode([], task=task)
            scheduled.append(ScheduledTask(task=task, priority=priority, mode=mode))
        scheduled.sort(key=lambda item: (-PRIORITY_ORDER.get(item.priority, 0), item.task.title.lower()))
        return scheduled
