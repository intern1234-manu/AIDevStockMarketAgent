from __future__ import annotations

import json
import os
from collections import deque
from typing import Any, Deque, Dict, List, Optional

from ..models import AgentResult, AgentTask


WORKER_PRIORITY_STANDARDS = {
    "history-analyzer": "high",
    "stage-build-sequence": "medium",
    "environment-checks": "critical",
    "paper-trading": "high",
    "shadow-mode": "critical",
    "live-mode": "critical",
    "observability-and-logs": "high",
    "model-diversity-checks": "high",
    "company-performance-agent": "high",
    "fundamental-agent": "high",
    "technical-agent": "high",
    "risk-sentiment-agent": "critical",
    "debate-controller": "medium",
    "master-agent": "high",
    "execution-agent": "critical",
}


WORKER_PROMPTS = {
    "history-analyzer": {
        "system_prompt": "You are the history analysis specialist. Review historical patterns, market regimes, and previous decision outcomes to identify lessons and risk signals relevant to the current task.",
        "output_schema": {
            "summary": "string",
            "key_findings": "list[string]",
            "confidence": "float",
            "risk_flags": "list[string]",
        },
    },
    "stage-build-sequence": {
        "system_prompt": "You are the delivery planner. Convert the task into a safe stage-based execution plan that respects engineering dependencies and production rollout safety.",
        "output_schema": {
            "summary": "string",
            "stages": "list[string]",
            "dependencies": "list[string]",
            "blocking_risks": "list[string]",
        },
    },
    "environment-checks": {
        "system_prompt": "You are the environment readiness specialist. Validate the runtime, dependencies, secrets, data sources, and infra prerequisites required for safe execution.",
        "output_schema": {
            "summary": "string",
            "checks_passed": "list[string]",
            "missing_items": "list[string]",
            "readiness": "string",
        },
    },
    "paper-trading": {
        "system_prompt": "You are the paper-trading validator. Simulate the trade flow in a low-risk environment and identify gaps in order logic, risk gates, and execution assumptions.",
        "output_schema": {
            "summary": "string",
            "simulation_steps": "list[string]",
            "risks_detected": "list[string]",
            "pass_status": "string",
        },
    },
    "shadow-mode": {
        "system_prompt": "You are the shadow-mode specialist. Run the task through live-like conditions without executing orders, and surface calibration issues before deployment.",
        "output_schema": {
            "summary": "string",
            "observations": "list[string]",
            "calibration_changes": "list[string]",
            "readiness": "string",
        },
    },
    "live-mode": {
        "system_prompt": "You are the deployment specialist. Prepare a production-ready plan with protective checks, kill switches, and rollback logic before live execution.",
        "output_schema": {
            "summary": "string",
            "rollout_steps": "list[string]",
            "guardrails": "list[string]",
            "rollback_plan": "list[string]",
        },
    },
    "observability-and-logs": {
        "system_prompt": "You are the observability specialist. Ensure the system remains diagnosable by monitoring health, metrics, log quality, and alerting conditions.",
        "output_schema": {
            "summary": "string",
            "metrics": "list[string]",
            "alerts": "list[string]",
            "health_status": "string",
        },
    },
    "model-diversity-checks": {
        "system_prompt": "You are the model diversity specialist. Confirm that the provider mix and agent assignments create meaningful independence rather than duplicated reasoning.",
        "output_schema": {
            "summary": "string",
            "provider_map": "list[string]",
            "independence_score": "float",
            "risks": "list[string]",
        },
    },
    "company-performance-agent": {
        "system_prompt": "You are the company performance intelligence agent. Review the company’s last five years of performance, current market news, and future strategic plans to assess how these factors could affect the stock’s trajectory and whether the business quality supports the thesis.",
        "output_schema": {
            "summary": "string",
            "symbol": "string",
            "performance_window": "string",
            "company_profile": "dict",
            "future_plan_summary": "string",
            "news_summary": "string",
            "agents_to_review": "list[string]",
        },
    },
    "fundamental-agent": {
        "system_prompt": "You are the fundamental research agent. Evaluate valuation, earnings quality, business fundamentals, and macro context to build a defensible thesis.",
        "output_schema": {
            "summary": "string",
            "thesis": "string",
            "supporting_factors": "list[string]",
            "risks": "list[string]",
        },
    },
    "technical-agent": {
        "system_prompt": "You are the technical analysis specialist. Review trend structure, momentum, volume, and price behavior to assess timing and trade quality.",
        "output_schema": {
            "summary": "string",
            "signal": "string",
            "supporting_indicators": "list[string]",
            "entry_conditions": "list[string]",
        },
    },
    "risk-sentiment-agent": {
        "system_prompt": "You are the risk and sentiment specialist. Assess volatility exposure, news sentiment, and operational risk before allowing any trade to proceed.",
        "output_schema": {
            "summary": "string",
            "risk_score": "float",
            "sentiment_summary": "string",
            "risk_controls": "list[string]",
        },
    },
    "debate-controller": {
        "system_prompt": "You are the debate coordinator. Structure the argument review, compare opposing viewpoints, and surface the strongest evidence before the final decision.",
        "output_schema": {
            "summary": "string",
            "arguments_for": "list[string]",
            "arguments_against": "list[string]",
            "recommended_direction": "string",
        },
    },
    "master-agent": {
        "system_prompt": "You are the master adjudicator. Combine the specialist arguments, apply decision rules, and decide whether the trade should pass, be reduced, or be vetoed.",
        "output_schema": {
            "summary": "string",
            "decision": "string",
            "confidence": "float",
            "veto_reasons": "list[string]",
        },
    },
    "execution-agent": {
        "system_prompt": "You are the execution specialist. Translate the approved decision into a valid trade plan with order type, risk controls, and broker-safe execution checks.",
        "output_schema": {
            "summary": "string",
            "order_plan": "string",
            "risk_controls": "list[string]",
            "execution_checks": "list[string]",
        },
    },
}


class BaseWorkerAgent:
    """Base class for all worker agents."""

    name = "BaseWorker"
    role = "worker"
    priority = "normal"
    system_prompt = "You are a helpful worker agent in a multi-agent trading system."
    output_schema: Dict[str, Any] = {
        "summary": "string",
        "details": "list[string]",
    }

    def __init__(self, state_dir: Optional[str] = None) -> None:
        self.state_dir = state_dir or os.getenv("WORKER_STATE_DIR", os.path.join(os.getcwd(), ".worker_state"))
        os.makedirs(self.state_dir, exist_ok=True)
        self.state_file = os.path.join(self.state_dir, f"{self.name.replace(' ', '_')}-state.json")
        self.task_queue: Deque[AgentTask] = deque()
        self.memory: Dict[str, Any] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.load_state()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.system_prompt = WORKER_PROMPTS.get(cls.name, {"system_prompt": cls.system_prompt})["system_prompt"]
        cls.output_schema = WORKER_PROMPTS.get(cls.name, {"output_schema": cls.output_schema})["output_schema"]
        cls.priority = WORKER_PRIORITY_STANDARDS.get(cls.name, getattr(cls, "priority", "normal"))

    def _serializable_task(self, task: AgentTask) -> Dict[str, Any]:
        return {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "context": task.context,
            "tags": task.tags,
        }

    def _restore_task(self, payload: Dict[str, Any]) -> AgentTask:
        return AgentTask(
            task_id=payload.get("task_id", ""),
            title=payload.get("title", ""),
            description=payload.get("description", ""),
            priority=payload.get("priority", "normal"),
            context=payload.get("context", {}),
            tags=payload.get("tags", []),
        )

    def persist_state(self) -> None:
        payload = {
            "memory": self.memory,
            "execution_history": self.execution_history,
            "task_queue": [self._serializable_task(task) for task in list(self.task_queue)],
        }
        with open(self.state_file, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=str)

    def load_state(self) -> None:
        if not os.path.exists(self.state_file):
            return
        with open(self.state_file, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        self.memory = payload.get("memory", {})
        self.execution_history = payload.get("execution_history", [])
        self.task_queue = deque(self._restore_task(task) for task in payload.get("task_queue", []))

    def enqueue(self, task: AgentTask) -> None:
        self.task_queue.append(task)
        self.persist_state()

    def dequeue(self) -> Optional[AgentTask]:
        if not self.task_queue:
            return None
        task = self.task_queue.popleft()
        self.persist_state()
        return task

    def peek_queue(self) -> Optional[AgentTask]:
        if not self.task_queue:
            return None
        return self.task_queue[0]

    def write_memory(self, key: str, value: Any) -> None:
        self.memory[key] = value
        self.persist_state()

    def read_memory(self, key: str, default: Any = None) -> Any:
        return self.memory.get(key, default)

    def record_execution(self, task: AgentTask, result: AgentResult) -> None:
        self.execution_history.append({
            "task_id": task.task_id,
            "agent_name": self.name,
            "status": result.status,
            "summary": result.summary,
            "details": result.details,
        })
        self.write_memory(f"result:{task.task_id}", result)

    def build_prompt(self, task: AgentTask) -> str:
        payload = {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "tags": task.tags,
            "context": task.context,
        }
        return (
            f"{self.system_prompt}\n\n"
            f"Task payload:\n{payload}\n\n"
            f"Return valid JSON matching this schema:\n{self.output_schema}"
        )

    def execute(self, task: AgentTask) -> AgentResult:
        prompt = self.build_prompt(task)
        result = AgentResult(
            agent_name=self.name,
            status="completed",
            task_id=task.task_id,
            summary=f"{self.name} reviewed task '{task.title}'.",
            details={
                "task": task.title,
                "description": task.description,
                "prompt": prompt,
                "schema": self.output_schema,
            },
        )
        self.record_execution(task, result)
        self.write_memory(f"last_result:{task.task_id}", result)
        return result
