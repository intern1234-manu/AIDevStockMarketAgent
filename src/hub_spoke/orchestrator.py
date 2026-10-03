from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

from .driver_agent import StockPlannerDriver
from .models import AgentTask


class HubSpokeOrchestrator:
    """Simple orchestrator that routes requests from a driver to worker agents."""

    def __init__(self) -> None:
        self.driver = StockPlannerDriver()

    def run(self, task: AgentTask, mode: str = "sequential") -> Dict[str, object]:
        worker_names = self.driver.classify_task(task)
        workers = [self.driver.workers[name] for name in worker_names]

        if mode == "parallel":
            with ThreadPoolExecutor(max_workers=len(workers) or 1) as executor:
                results = list(executor.map(lambda agent: agent.execute(task), workers))
        else:
            results = [agent.execute(task) for agent in workers]

        return {
            "driver": self.driver.__class__.__name__,
            "task_id": task.task_id,
            "title": task.title,
            "assigned_workers": worker_names,
            "mode": mode,
            "results": [
                {
                    "agent": item.agent_name,
                    "status": item.status,
                    "summary": item.summary,
                    "details": item.details,
                }
                for item in results
            ],
        }

    def run_many(self, tasks: List[AgentTask], mode: str = "sequential") -> List[Dict[str, object]]:
        return [self.run(task, mode=mode) for task in tasks]
