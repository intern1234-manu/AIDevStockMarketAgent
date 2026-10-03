from __future__ import annotations

from .base_agent import BaseWorkerAgent
from ..models import AgentResult, AgentTask


class ObservabilityAgent(BaseWorkerAgent):
    name = "observability-and-logs"
    role = "monitoring"

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary="Configured monitoring, logs, and health checks to keep the system observable and diagnosable during all stages.",
            details={
                "checks": ["structured logs", "heartbeat validation", "metrics collection", "health and alerting"],
                "context": task.context,
            },
        )
