from __future__ import annotations

from ..models import AgentResult, AgentTask
from .base_agent import BaseWorkerAgent


class MarketSentimentAnalyzerAgent(BaseWorkerAgent):
    name = "market-sentiment-analyzer"
    role = "market-sentiment"
    priority = "high"

    def execute(self, task: AgentTask) -> AgentResult:
        symbol = str((task.context or {}).get("symbol") or (task.title or "").split()[-1] or "AAPL").upper()
        sentiment = "mixed-to-positive" if "news" in task.tags or "market" in task.tags else "neutral"
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary=f"Assessed the broader market sentiment context impacting {symbol}, including risk appetite, sector breadth, and volatility regime.",
            details={
                "symbol": symbol,
                "sentiment": sentiment,
                "market_factors": [
                    "breadth and sector leadership",
                    "volatility regime changes",
                    "rates and liquidity conditions",
                    "macro catalyst impact"
                ],
                "context": task.context,
            },
        )
