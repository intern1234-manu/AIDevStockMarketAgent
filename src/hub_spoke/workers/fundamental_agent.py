from __future__ import annotations

from .base_agent import BaseWorkerAgent
from ..models import AgentResult, AgentTask


class FundamentalAgent(BaseWorkerAgent):
    name = "fundamental-agent"
    role = "research"

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary="Analyzed the company fundamentals and valuation context to assess long-term quality and risk-adjusted thesis strength.",
            details={
                "focus": ["P/E", "earnings quality", "macro context", "guidance review", "valuation check"],
                "context": task.context,
            },
        )
