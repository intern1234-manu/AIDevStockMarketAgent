from __future__ import annotations

from .base_agent import BaseWorkerAgent
from ..models import AgentResult, AgentTask


class StageBuildSequenceAgent(BaseWorkerAgent):
    name = "stage-build-sequence"
    role = "planning"

    def execute(self, task: AgentTask) -> AgentResult:
        sequence = [
            "Resolve business and risk constraints",
            "Environment setup and dependency checks",
            "Deterministic gates and safety validation",
            "Data layer validation",
            "Agent integration and schema validation",
            "Paper trading verification",
            "Shadow mode testing",
            "Live mode rollout",
        ]
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary="Mapped the project into engineering stages and confirmed the safe sequence for rollout.",
            details={"sequence": sequence, "context": task.context},
        )
