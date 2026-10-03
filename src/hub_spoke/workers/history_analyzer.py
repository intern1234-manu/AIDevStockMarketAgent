from __future__ import annotations

from .base_agent import BaseWorkerAgent
from ..models import AgentResult, AgentTask


class HistoryAnalyzerAgent(BaseWorkerAgent):
    name = "history-analyzer"
    role = "analysis"

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary="Reviewed historical context, prior decisions, and patterns to determine whether the strategy needs calibration.",
            details={
                "focus": ["backtest review", "market regime analysis", "decision pattern assessment"],
                "context": task.context,
            },
        )
