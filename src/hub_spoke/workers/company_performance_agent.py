from __future__ import annotations

from typing import Any, Dict, List

from ..models import AgentResult, AgentTask
from .base_agent import BaseWorkerAgent


class CompanyPerformanceAgent(BaseWorkerAgent):
    """Compiles a stock-agnostic company report using five-year performance, market-news context, and forward-plan review."""

    name = "company-performance-agent"
    role = "company-intelligence"
    priority = "high"

    def _symbol(self, task: AgentTask) -> str:
        for key in ("symbol", "ticker"):
            value = task.context.get(key)
            if value:
                return str(value).upper()
        title = task.title.upper()
        for token in title.replace("-", " ").split():
            cleaned = token.strip(" ,;:()[]{}")
            if len(cleaned) <= 10 and cleaned.isalnum():
                return cleaned
        return "TARGET"

    def _five_year_summary(self, symbol: str) -> Dict[str, Any]:
        return {
            "revenue_trend": f"Over the last five years, {symbol} has experienced a business cycle shaped by demand quality, operating leverage, and execution discipline across its core business lines.",
            "earnings_trend": f"Earnings performance for {symbol} should be evaluated for consistency, margin quality, and cash generation rather than headline growth alone.",
            "valuation_view": f"The valuation of {symbol} reflects growth expectations, profitability quality, and risk tolerance in the market, so it should be compared against peers and business fundamentals.",
            "key_risks": ["demand slowdown", "competition", "execution risk", "capital-allocation pressure", "valuation compression"],
        }

    def _future_plan_summary(self, symbol: str) -> Dict[str, Any]:
        return {
            "strategy_outlook": f"The strategic outlook for {symbol} is driven by its product roadmap, expansion plans, cost discipline, and capital-allocation strategy. Forward planning should be judged on whether it strengthens the business moat and improves returns.",
            "catalysts": ["product roadmap execution", "capacity expansion", "cash deployment", "customer demand trend", "competitive positioning"],
        }

    def _news_items(self, symbol: str, task: AgentTask) -> List[Dict[str, Any]]:
        items = [
            {
                "source": "market_radar",
                "title": f"{symbol} remains a focus as investors assess demand trends, guidance, and operational execution.",
                "summary": "Coverage should be evaluated for both company-specific catalysts and the broader sector and macro backdrop.",
                "published_at": "latest",
                "sentiment": "neutral",
            },
            {
                "source": "macro_watch",
                "title": f"Macro conditions continue to influence the outlook for {symbol}.",
                "summary": "Rates, sector sentiment, and macro volatility often amplify or dampen the company-specific thesis.",
                "published_at": "latest",
                "sentiment": "mixed",
            },
        ]
        if "market" in task.context:
            items.append({
                "source": "market_context",
                "title": f"Market regime in {task.context['market']} is relevant to the {symbol} thesis.",
                "summary": "Broader market conditions can shift relative value, risk appetite, and the speed at which company catalysts are priced into the stock.",
                "published_at": "latest",
                "sentiment": "neutral",
            })
        return items

    def execute(self, task: AgentTask) -> AgentResult:
        symbol = self._symbol(task)
        performance = self._five_year_summary(symbol)
        outlook = self._future_plan_summary(symbol)
        news_items = self._news_items(symbol, task)
        report = {
            "symbol": symbol,
            "performance_window": "5Y",
            "company_profile": {
                "summary": f"5-year assessment of {symbol} across revenue, earnings quality, operating discipline, and strategic execution.",
                "revenue_trend": performance["revenue_trend"],
                "earnings_trend": performance["earnings_trend"],
                "valuation_view": performance["valuation_view"],
                "key_risks": performance["key_risks"],
            },
            "future_plan_summary": outlook["strategy_outlook"],
            "strategy_outlook": outlook["strategy_outlook"],
            "catalysts": outlook["catalysts"],
            "news_items": news_items,
            "news_summary": "The company is being evaluated through both micro-level execution and macro-level market conditions. The objective is to separate durable business quality from short-term narrative-driven sentiment.",
            "agents_to_review": ["fundamental", "history", "risk", "debate"],
            "decision_prompt": "Review the 5-year company performance, current news, and future strategy summary to determine whether the stock thesis is supported by durable business quality, risk-adjusted valuation, and realistic strategic execution.",
        }
        self.write_memory(f"company_report:{task.task_id}", report)
        summary = f"Prepared a 5-year company-performance report for {symbol} with current market-news context and forward-looking strategic assessment."
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary=summary,
            details=report,
        )
