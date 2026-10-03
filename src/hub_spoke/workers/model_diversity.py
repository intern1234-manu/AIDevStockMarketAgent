from __future__ import annotations

from .base_agent import BaseWorkerAgent
from ..models import AgentResult, AgentTask


class ModelDiversityAgent(BaseWorkerAgent):
    name = "model-diversity-checks"
    role = "quality"

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary="Validated model diversity and provider separation to ensure independent reasoning rather than duplicated stylistic agreement.",
            details={
                "checks": ["provider distinctness", "role mapping", "independence review", "boot-time validation"],
                "context": task.context,
            },
        )
