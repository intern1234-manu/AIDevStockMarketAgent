from __future__ import annotations

from .base_agent import BaseWorkerAgent
from ..models import AgentResult, AgentTask


class DebateControllerAgent(BaseWorkerAgent):
    name = "debate-controller"
    role = "coordination"

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary="Coordinated challenge rounds, compared opposing positions, and prepared a concise review of the most relevant trade arguments.",
            details={
                "focus": ["challenge round management", "position synthesis", "argument review", "decision framing"],
                "context": task.context,
            },
        )
