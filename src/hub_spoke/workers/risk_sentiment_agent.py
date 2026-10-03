from __future__ import annotations

from .base_agent import BaseWorkerAgent
from ..models import AgentResult, AgentTask


class RiskSentimentAgent(BaseWorkerAgent):
    name = "risk-sentiment-agent"
    role = "risk"

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary="Evaluated risk constraints, sentiment, and market headlines to determine whether the thesis remains acceptable under stress.",
            details={
                "focus": ["risk limits", "news sentiment", "event risk", "volatility watch", "portfolio exposure"],
                "context": task.context,
            },
        )
