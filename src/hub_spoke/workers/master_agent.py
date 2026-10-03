from __future__ import annotations

from .base_agent import BaseWorkerAgent
from ..models import AgentResult, AgentTask


class MasterAgent(BaseWorkerAgent):
    name = "master-agent"
    role = "decision"

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary="Adjudicated the competing agent views, applied tie-break logic, and confirmed whether the decision should proceed or be blocked.",
            details={
                "focus": ["adjudication", "tie-break", "veto check", "final decision"],
                "context": task.context,
            },
        )
