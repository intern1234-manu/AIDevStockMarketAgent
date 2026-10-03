from __future__ import annotations

from .base_agent import BaseWorkerAgent
from ..models import AgentResult, AgentTask


class PaperTradingAgent(BaseWorkerAgent):
    name = "paper-trading"
    role = "simulation"

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary="Prepared paper-trading validation for order routing, stop logic, and risk gate testing without real capital exposure.",
            details={
                "actions": ["validate order flow", "test bracket orders", "check risk veto behavior", "verify paper account setup"],
                "context": task.context,
            },
        )
