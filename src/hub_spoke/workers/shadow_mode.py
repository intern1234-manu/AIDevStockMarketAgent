from __future__ import annotations

from .base_agent import BaseWorkerAgent
from ..models import AgentResult, AgentTask


class ShadowModeAgent(BaseWorkerAgent):
    name = "shadow-mode"
    role = "simulation"

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary="Set up shadow-mode validation to run against live data without placing orders, allowing calibration before deployment.",
            details={
                "actions": ["live data monitoring", "no-order validation", "circuit breaker calibration", "decision review"],
                "context": task.context,
            },
        )
