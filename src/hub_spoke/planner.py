from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models import AgentTask
from .task_scheduler import PRIORITY_ORDER
from .worker_graph import resolve_execution_order

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None


@dataclass
class PlannerDecision:
    assigned_workers: List[str] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    reasoning: str = ""
    requires_parallel: bool = False
    priority: str = "normal"
    state: str = "analysis"


STATE_ROUTING: Dict[str, List[str]] = {
    "analysis": ["news", "chart", "sentiment", "company", "history", "fundamental", "technical", "model"],
    "research": ["news", "chart", "sentiment", "company", "history", "fundamental", "technical", "model"],
    "market_news": ["news", "chart", "sentiment", "company", "history", "fundamental", "technical", "model"],
    "market_analysis": ["news", "chart", "sentiment", "company", "history", "fundamental", "technical", "model"],
    "risk_review": ["news", "chart", "sentiment", "company", "history", "fundamental", "technical", "risk", "debate", "master"],
    "risk_validation": ["news", "chart", "sentiment", "company", "history", "fundamental", "technical", "risk", "debate", "master"],
    "approval": ["risk", "debate", "master"],
    "broker_execution": ["news", "chart", "sentiment", "company", "history", "fundamental", "technical", "risk", "execution", "observability"],
    "execution": ["news", "chart", "sentiment", "company", "history", "fundamental", "technical", "risk", "execution", "observability"],
    "paper_trading": ["environment", "risk", "paper", "observability"],
    "shadow_trading": ["risk", "paper", "shadow", "observability"],
    "live_trading": ["risk", "execution", "live", "observability"],
    "monitoring": ["observability"],
}


WORKER_PRIORITY_STANDARDS = {
    "news": "high",
    "company": "high",
    "chart": "high",
    "sentiment": "high",
    "history": "high",
    "build": "medium",
    "environment": "critical",
    "paper": "high",
    "shadow": "critical",
    "live": "critical",
    "observability": "high",
    "model": "high",
    "fundamental": "high",
    "technical": "high",
    "risk": "critical",
    "debate": "medium",
    "master": "high",
    "execution": "critical",
}


def infer_task_priority(task: AgentTask) -> str:
    value = (task.priority or "normal").strip().lower()
    text = f"{task.title} {task.description} {' '.join(task.tags)}".lower()
    if value in PRIORITY_ORDER:
        return value
    if any(term in text for term in ["live", "broker", "execution", "risk", "loss", "veto", "production"]):
        return "critical"
    if any(term in text for term in ["paper", "shadow", "monitor", "sentiment", "model", "strategy", "trade"]):
        return "high"
    if any(term in text for term in ["stage", "plan", "review", "setup", "analysis", "roadmap"]):
        return "medium"
    return "normal"


def normalize_route_state(value: Any) -> str:
    state = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return state if state else ""


def infer_route_state(task: AgentTask) -> str:
    context = task.context or {}
    explicit_state_value = task.state if task.state is not None else context.get("workflow_state") or context.get("state")
    explicit_state = normalize_route_state(explicit_state_value)
    if explicit_state and explicit_state in STATE_ROUTING:
        return explicit_state

    text = f"{task.title} {task.description} {' '.join(task.tags)}".lower()
    if any(term in text for term in ["paper", "simulate", "sandbox", "demo"]):
        return "paper_trading"
    if any(term in text for term in ["shadow", "dry run", "live-like"]):
        return "shadow_trading"
    if any(term in text for term in ["live", "launch", "production", "deploy"]):
        return "live_trading"
    if any(term in text for term in ["broker", "route", "order", "execution", "trade", "submit"]):
        return "broker_execution"
    if any(term in text for term in ["risk", "volatility", "sentiment", "veto", "drawdown", "position"]):
        return "risk_review"
    if any(term in text for term in ["monitor", "observability", "metrics", "health", "alert"]):
        return "monitoring"
    return "analysis"


def route_for_state(task: AgentTask) -> List[str]:
    state = infer_route_state(task)
    workers = STATE_ROUTING.get(state, STATE_ROUTING["analysis"])
    return list(dict.fromkeys(workers))


class LLMTaskPlanner:
    """Planner that prefers an LLM when configured, but falls back to heuristic routing."""

    def __init__(self, model: Optional[str] = None) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.client = None
        if OpenAI and self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.base_url else OpenAI(api_key=self.api_key)

    @staticmethod
    def heuristic_plan(task: AgentTask) -> List[str]:
        text = f"{task.title} {task.description} {' '.join(task.tags)}".lower()
        assigned: List[str] = []

        keyword_map = {
            "news": ["news", "headline", "coverage", "press", "announcement", "newsflow", "breaking"],
            "company": ["company", "performance", "5y", "five year", "five-year", "revenue", "guidance", "strategy", "future plan", "roadmap"],
            "chart": ["chart", "technical", "trend", "moving average", "support", "resistance", "momentum", "price action"],
            "sentiment": ["sentiment", "market mood", "risk appetite", "breadth", "volatility", "macro"],
            "history": ["history", "backtest", "past", "analysis", "performance"],
            "build": ["build", "sequence", "stage", "milestone", "roadmap", "plan"],
            "environment": ["environment", "setup", "config", "dependency", "check", "infra"],
            "paper": ["paper", "simulate", "sandbox", "demo"],
            "shadow": ["shadow", "dry run", "live data", "no order"],
            "live": ["live", "production", "deploy", "launch"],
            "observability": ["log", "observability", "metrics", "monitor", "health"],
            "model": ["model", "diversity", "provider", "independent", "heterogeneous"],
            "fundamental": ["fundamental", "valuation", "earnings", "balance sheet", "revenue", "guidance", "quality"],
            "technical": ["technical", "trend", "indicator", "moving average", "price action", "support", "resistance", "momentum"],
            "risk": ["risk", "sentiment", "news", "volatility", "headline", "exposure", "portfolio"],
            "debate": ["debate", "challenge", "discuss", "review", "argument", "round"],
            "master": ["master", "final", "decision", "adjudicate", "tie-break", "veto", "approve"],
            "execution": ["execution", "order", "broker", "trade", "submit", "route"],
        }

        for worker_name, keywords in keyword_map.items():
            if any(keyword in text for keyword in keywords):
                assigned.append(worker_name)

        if not assigned:
            assigned = ["fundamental", "technical", "risk", "debate", "master", "execution"]

        return list(dict.fromkeys(assigned))

    @staticmethod
    def _sanitize_workers(workers: Any) -> List[str]:
        if not isinstance(workers, list):
            return []
        cleaned = []
        for item in workers:
            value = str(item).strip()
            if value:
                cleaned.append(value)
        return cleaned

    def build_prompt(self, task: AgentTask) -> str:
        return f"""
You are the task planner for a multi-agent stock trading system.
Your job is to assign a task to the best worker agents.

Follow the industry-standard trading flow:
1) market data and baseline analysis (history)
2) research and signal generation (fundamental, technical, model)
3) risk and sentiment validation (risk)
4) debate / challenge / approval (debate, master)
5) execution and broker-safe route (execution)
6) staging gates for paper, shadow, and live rollout

Available workers:
- company
- history
- build
- environment
- paper
- shadow
- live
- observability
- model
- fundamental
- technical
- risk
- debate
- master
- execution

Task details:
- ID: {task.task_id}
- Title: {task.title}
- Description: {task.description}
- Priority: {task.priority}
- Tags: {', '.join(task.tags) if task.tags else 'none'}
- Context: {json.dumps(task.context, default=str)}

Return valid JSON only with this structure:
{{
  "assigned_workers": ["worker_name_1", "worker_name_2"],
  "reasoning": "short explanation",
  "execution_order": ["worker_name_1", "worker_name_2"],
  "requires_parallel": true
}}
"""

    def _parse_llm_payload(self, content: str) -> PlannerDecision:
        payload: Dict[str, Any] = {}
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1)
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            prefix = content.split("{", 1)
            suffix = content.rsplit("}", 1)
            if len(prefix) > 1 and len(suffix) > 1:
                try:
                    payload = json.loads(prefix[1].rsplit("}", 1)[0] if False else "{" + suffix[0].split("{", 1)[1])
                except Exception:
                    payload = {}

        assigned_workers = self._sanitize_workers(payload.get("assigned_workers"))
        execution_order = self._sanitize_workers(payload.get("execution_order"))
        if not assigned_workers and execution_order:
            assigned_workers = execution_order
        if not execution_order and assigned_workers:
            execution_order = resolve_execution_order(assigned_workers)
        if not assigned_workers:
            assigned_workers = self.heuristic_plan(AgentTask(task_id="fallback", title="", description="", tags=[]))
        if not execution_order:
            execution_order = resolve_execution_order(assigned_workers)

        return PlannerDecision(
            assigned_workers=assigned_workers,
            execution_order=execution_order,
            reasoning=str(payload.get("reasoning", "")),
            requires_parallel=bool(payload.get("requires_parallel", False)),
            priority=infer_task_priority(task),
        )

    def plan_task(self, task: AgentTask) -> PlannerDecision:
        state = infer_route_state(task)
        state_workers = route_for_state(task)
        if state_workers:
            ordered = resolve_execution_order(state_workers)
            return PlannerDecision(
                assigned_workers=state_workers,
                execution_order=ordered,
                reasoning=f"State-based routing used the {state} market workflow and broker-safe execution order.",
                priority=infer_task_priority(task),
                state=state,
            )

        if not self.client:
            workers = self.heuristic_plan(task)
            return PlannerDecision(
                assigned_workers=workers,
                execution_order=resolve_execution_order(workers),
                reasoning="Heuristic driver planner selected workers using keyword routing and dependency ordering.",
                priority=infer_task_priority(task),
                state=state,
            )

        prompt = self.build_prompt(task)
        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": "You are a careful planner for autonomous trading workflow orchestration."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )
            content = getattr(response, "output_text", None) or ""
            if not content:
                raise ValueError("Empty model response")
            decision = self._parse_llm_payload(content)
            decision.priority = infer_task_priority(task)
            return decision
        except Exception:
            workers = self.heuristic_plan(task)
            return PlannerDecision(
                assigned_workers=workers,
                execution_order=resolve_execution_order(workers),
                reasoning="LLM planner unavailable; heuristic fallback used with dependency-aware ordering.",
                priority=infer_task_priority(task),
            )

    def plan(self, task: AgentTask) -> List[str]:
        decision = self.plan_task(task)
        return decision.execution_order or decision.assigned_workers
