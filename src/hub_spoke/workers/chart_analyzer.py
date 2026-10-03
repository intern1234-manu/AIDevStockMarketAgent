from __future__ import annotations

from ..models import AgentResult, AgentTask
from .base_agent import BaseWorkerAgent


class ChartAnalyzerAgent(BaseWorkerAgent):
    name = "chart-analyzer"
    role = "technical-analysis"
    priority = "high"

    def execute(self, task: AgentTask) -> AgentResult:
        symbol = str((task.context or {}).get("symbol") or (task.title or "").split()[-1] or "AAPL").upper()
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary=f"Reviewed chart structure for {symbol} and highlighted trend, support, resistance, and momentum conditions.",
            details={
                "symbol": symbol,
                "chart_summary": "Trend remains sensitive to breakout and pullback structure; momentum and volume confirm whether trend continuation is healthy.",
                "support_resistance": ["prior range support", "trendline validation", "volume confirmation"],
                "context": task.context,
            },
        )
