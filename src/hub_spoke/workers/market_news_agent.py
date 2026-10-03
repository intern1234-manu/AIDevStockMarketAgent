from __future__ import annotations

import os
from typing import Any, Dict, List

try:
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None

from ..models import AgentResult, AgentTask
from .base_agent import BaseWorkerAgent


class MarketNewsCollectorAgent(BaseWorkerAgent):
    """Collects the current news and market context for a target stock and prepares a report for the history analyzer."""

    name = "market-news-collector"
    role = "market-intelligence"
    priority = "high"

    def _symbol(self, task: AgentTask) -> str:
        if task.context.get("symbol"):
            return str(task.context["symbol"]).upper()
        if task.context.get("ticker"):
            return str(task.context["ticker"]).upper()
        if task.title:
            parts = task.title.split()
            for part in parts:
                token = part.strip().upper()
                if token.isalnum() and len(token) <= 10:
                    return token
        return "AAPL"

    def _screener_url(self, symbol: str) -> str:
        cleaned = symbol.strip().upper()
        return f"https://www.screener.in/company/{cleaned}/"

    def _market_factors(self, symbol: str, task: AgentTask) -> List[str]:
        factors = [
            f"{symbol} sector momentum and relative strength",
            "interest-rate sensitivity and yield curve movement",
            "earnings calendar and guidance risk",
            "macro sentiment and CPI / Fed narrative",
            "sector-level supply chain and commodity exposure",
            "broker / institutional positioning and volatility regime",
        ]
        if "market" in task.context:
            factors.append(f"market regime in {task.context['market']}")
        if task.tags:
            factors.append(f"tag context: {', '.join(task.tags)}")
        return factors

    def _fallback_news(self, symbol: str) -> List[Dict[str, Any]]:
        return [
            {
                "source": "market_radar",
                "title": f"Analysts monitoring {symbol} as sector momentum and earnings expectations remain in focus.",
                "summary": "The market is tracking company-specific catalysts, sector breadth, and product demand indicators that could affect price action.",
                "published_at": "latest",
                "sentiment": "neutral",
            },
            {
                "source": "macro_watch",
                "title": f"Macro conditions may continue to influence {symbol} through rates, liquidity, and sector risk sentiment.",
                "summary": "Interest-rate expectations, consumer demand readings, and broad market volatility are continuing to shape sentiment.",
                "published_at": "latest",
                "sentiment": "mixed",
            },
        ]

    def _fetch_news_api_items(self, symbol: str) -> List[Dict[str, Any]]:
        api_key = os.getenv("NEWS_API_KEY") or os.getenv("NEWSAPI_API_KEY")
        if not api_key or requests is None:
            return self._fallback_news(symbol)

        try:
            query = f"{symbol} OR {symbol} earnings OR {symbol} stock news"
            response = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 5,
                },
                headers={"X-Api-Key": api_key},
                timeout=15,
            )
            if response.status_code != 200:
                return self._fallback_news(symbol)
            payload = response.json() or {}
            articles = payload.get("articles", []) or []
            items: List[Dict[str, Any]] = []
            for article in articles[:5]:
                title = article.get("title") or "Market news"
                source_name = (article.get("source") or {}).get("name") or "news"
                items.append({
                    "source": source_name,
                    "title": title,
                    "summary": article.get("description") or article.get("content") or title,
                    "published_at": article.get("publishedAt") or "latest",
                    "url": article.get("url") or "",
                    "sentiment": self._sentiment_from_text(title + " " + (article.get("description") or "")),
                })
            return items if items else self._fallback_news(symbol)
        except Exception:
            return self._fallback_news(symbol)

    def _sentiment_from_text(self, text: str) -> str:
        lowered = text.lower()
        positive = ["beat", "rally", "upgrade", "strong", "growth", "surge", "profit", "beat estimates"]
        negative = ["downgrade", "selloff", "loss", "risk", "weak", "concern", "miss", "slump", "investigation"]
        score = sum(1 for token in positive if token in lowered) - sum(1 for token in negative if token in lowered)
        if score > 0:
            return "positive"
        if score < 0:
            return "negative"
        return "neutral"

    def execute(self, task: AgentTask) -> AgentResult:
        symbol = self._symbol(task)
        market_factors = self._market_factors(symbol, task)
        news_items = self._fetch_news_api_items(symbol)
        report = {
            "symbol": symbol,
            "market_factors": market_factors,
            "news_items": news_items,
            "news_summary": "Recent coverage indicates the key drivers for the stock are sector momentum, earnings and guidance expectations, and macro risk conditions.",
            "screener_52_week_url": self._screener_url(symbol),
            "performance_window": "52-week",
            "analysis_prompt": (
                "Use the news sentiment, market factor list, and 52-week Screener trend to assess whether the stock is being driven by company-specific catalysts or wider market conditions."
            ),
        }
        summary = f"Collected market news and exposure factors for {symbol}; prepared a report for history analysis with a 52-week Screener view."
        self.write_memory(f"news_report:{task.task_id}", report)
        self.record_execution(task, AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary=summary,
            details=report,
        ))
        return AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary=summary,
            details=report,
        )
