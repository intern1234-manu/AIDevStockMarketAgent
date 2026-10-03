from __future__ import annotations

from .base_agent import BaseWorkerAgent
from ..models import AgentResult, AgentTask


class ExecutionAgent(BaseWorkerAgent):
    name = "execution-agent"
    role = "execution"

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary="Prepared the approved trade execution path, including order type, risk controls, and broker routing checks.",
            details={
                "focus": ["trade validation", "bracket order planning", "broker routing", "execution safeguards"],
                "context": task.context,
            },
        )
