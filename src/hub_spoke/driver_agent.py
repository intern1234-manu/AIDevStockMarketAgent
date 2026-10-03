from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

from .models import AgentTask
from .planner import LLMTaskPlanner
from .task_scheduler import TaskScheduler
from .worker_graph import resolve_execution_order, resolve_parallel_stages
from .workers import (
    ChartAnalyzerAgent,
    DebateControllerAgent,
    EnvironmentChecksAgent,
    ExecutionAgent,
    FundamentalAgent,
    HistoryAnalyzerAgent,
    LiveModeAgent,
    MarketNewsCollectorAgent,
    CompanyPerformanceAgent,
    MarketSentimentAnalyzerAgent,
    MasterAgent,
    ModelDiversityAgent,
    ObservabilityAgent,
    PaperTradingAgent,
    RiskSentimentAgent,
    ShadowModeAgent,
    StageBuildSequenceAgent,
    TechnicalAgent,
)


class StockPlannerDriver:
    """Driver agent that interprets user tasks and assigns work to specialized workers."""

    def __init__(self) -> None:
        self.planner = LLMTaskPlanner()
        self.workers = {
            "history": HistoryAnalyzerAgent(),
            "build": StageBuildSequenceAgent(),
            "environment": EnvironmentChecksAgent(),
            "paper": PaperTradingAgent(),
            "shadow": ShadowModeAgent(),
            "live": LiveModeAgent(),
            "observability": ObservabilityAgent(),
            "model": ModelDiversityAgent(),
            "fundamental": FundamentalAgent(),
            "technical": TechnicalAgent(),
            "risk": RiskSentimentAgent(),
            "debate": DebateControllerAgent(),
            "master": MasterAgent(),
            "execution": ExecutionAgent(),
            "news": MarketNewsCollectorAgent(),
            "company": CompanyPerformanceAgent(),
            "chart": ChartAnalyzerAgent(),
            "sentiment": MarketSentimentAnalyzerAgent(),
        }

    def resolve_execution_order(self, worker_names: List[str]) -> List[str]:
        return resolve_execution_order(worker_names)

    def classify_task(self, task: AgentTask) -> List[str]:
        decision = self.planner.plan_task(task)
        ordered = decision.execution_order or self.resolve_execution_order(decision.assigned_workers)
        if task.state or task.context.get("workflow_state") or task.context.get("state"):
            return ordered
        return ordered

    def classify_task_with_priority(self, task: AgentTask):
        decision = self.planner.plan_task(task)
        return decision

    def _run_worker(self, worker, task: AgentTask, mode: str):
        worker.enqueue(task)
        worker.write_memory(f"last_task:{task.task_id}", {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "scheduled_mode": mode,
        })
        result = worker.execute(task)
        worker.record_execution(task, result)
        return result

    def execute_parallel(self, task: AgentTask, worker_names: List[str]) -> Dict[str, object]:
        mode = "parallel"
        stages = resolve_parallel_stages(worker_names)
        results = []

        for stage in stages:
            stage_workers = [self.workers[name] for name in stage if name in self.workers]
            if not stage_workers:
                continue
            with ThreadPoolExecutor(max_workers=max(1, len(stage_workers))) as executor:
                batch_results = list(executor.map(lambda worker: self._run_worker(worker, task, mode), stage_workers))
            results.extend(batch_results)

        return {
            "driver": self.__class__.__name__,
            "task_id": task.task_id,
            "title": task.title,
            "assigned_workers": worker_names,
            "results": [
                {
                    "agent": item.agent_name,
                    "status": item.status,
                    "summary": item.summary,
                    "details": item.details,
                }
                for item in results
            ],
        }

    def execute(self, task: AgentTask) -> Dict[str, object]:
        decision = self.classify_task_with_priority(task)
        worker_names = decision.execution_order or self.resolve_execution_order(decision.assigned_workers)
        mode = TaskScheduler.decide_mode(worker_names, force="parallel" if decision.requires_parallel else None)
        if mode == "parallel":
            return self.execute_parallel(task, worker_names)

        results = []
        for worker_name in worker_names:
            worker = self.workers[worker_name]
            results.append(self._run_worker(worker, task, mode))

        return {
            "driver": self.__class__.__name__,
            "task_id": task.task_id,
            "title": task.title,
            "assigned_workers": worker_names,
            "results": [
                {
                    "agent": item.agent_name,
                    "status": item.status,
                    "summary": item.summary,
                    "details": item.details,
                }
                for item in results
            ],
        }
