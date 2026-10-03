from __future__ import annotations

from .base_agent import BaseWorkerAgent
from ..models import AgentResult, AgentTask


class TechnicalAgent(BaseWorkerAgent):
    name = "technical-agent"
    role = "analysis"

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary="Reviewed price action, indicators, volume, and trend structure to assess entry quality and trade timing.",
            details={
                "focus": ["trend structure", "support/resistance", "momentum", "volume confirmation", "pattern review"],
                "context": task.context,
            },
        )
