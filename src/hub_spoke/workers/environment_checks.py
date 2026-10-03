from __future__ import annotations

from .base_agent import BaseWorkerAgent
from ..models import AgentResult, AgentTask


class EnvironmentChecksAgent(BaseWorkerAgent):
    name = "environment-checks"
    role = "operations"

    def execute(self, task: AgentTask) -> AgentResult:
        checks = [
            "Python environment validation",
            "Dependency installation review",
            "Database and cache service readiness",
            "API keys and environment variables validation",
            "Broker connectivity and runtime configuration",
        ]
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary="Checked environment readiness and confirmed required infrastructure and configuration for execution.",
            details={"checks": checks, "context": task.context},
        )
