from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .queue import QueueTask


@dataclass
class WorkflowStage:
    stage_id: str
    name: str
    description: str
    workers: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    parallel_allowed: bool = False


STOCK_TRADING_ROADMAP: List[WorkflowStage] = [
    WorkflowStage(
        stage_id="stage-0",
        name="resolve-before-touching-code",
        description="Answer critical operating constraints before implementation: max drawdown, max position size, earnings blackout, watchlist, and broker readiness.",
        workers=["history", "build", "environment"],
        dependencies=[],
        parallel_allowed=False,
    ),
    WorkflowStage(
        stage_id="stage-1",
        name="environment-and-infrastructure",
        description="Create the environment, install dependencies, start Postgres/Redis, validate secrets, and check broker connectivity.",
        workers=["environment"],
        dependencies=["stage-0"],
        parallel_allowed=False,
    ),
    WorkflowStage(
        stage_id="stage-2",
        name="deterministic-gates-first",
        description="Write and validate deterministic rules before any model-based reasoning: risk veto, circuit breakers, bracket recovery, and safety gates.",
        workers=["build", "model", "risk"],
        dependencies=["stage-1"],
        parallel_allowed=True,
    ),
    WorkflowStage(
        stage_id="stage-3",
        name="data-layer-validation",
        description="Validate the free data layer using yfinance, NewsAPI, VADER, and source validation so no claim is accepted without traceability.",
        workers=["history", "fundamental", "technical", "risk"],
        dependencies=["stage-2"],
        parallel_allowed=True,
    ),
    WorkflowStage(
        stage_id="stage-4",
        name="agent-integration-and-schema-validation",
        description="Connect the agent layer, validate schemas, and ensure outputs are checked and logged.",
        workers=["debate", "master", "execution"],
        dependencies=["stage-3"],
        parallel_allowed=True,
    ),
    WorkflowStage(
        stage_id="stage-5",
        name="paper-trading",
        description="Run the system against paper trading to validate order flow, stop logic, and risk gates without live capital risk.",
        workers=["paper", "observability"],
        dependencies=["stage-4"],
        parallel_allowed=True,
    ),
    WorkflowStage(
        stage_id="stage-6",
        name="shadow-mode",
        description="Use live-like market conditions without submitting orders to calibrate the system and improve risk thresholds.",
        workers=["shadow", "observability", "model"],
        dependencies=["stage-5"],
        parallel_allowed=True,
    ),
    WorkflowStage(
        stage_id="stage-7",
        name="live-mode-rollout",
        description="Go live only after paper and shadow phases pass with stable behavior and no unresolved risk issues.",
        workers=["live", "execution", "observability"],
        dependencies=["stage-6"],
        parallel_allowed=False,
    ),
]


def build_stock_trading_queue() -> List[QueueTask]:
    tasks: List[QueueTask] = []
    for stage in STOCK_TRADING_ROADMAP:
        tasks.append(
            QueueTask(
                task_id=stage.stage_id,
                title=stage.name,
                description=stage.description,
                priority="high" if stage.stage_id in {"stage-5", "stage-6", "stage-7"} else "normal",
                dependencies=stage.dependencies,
                workers=stage.workers,
                metadata={"stage_id": stage.stage_id, "parallel_allowed": stage.parallel_allowed},
            )
        )
    return tasks


def get_stage_by_id(stage_id: str) -> WorkflowStage:
    for stage in STOCK_TRADING_ROADMAP:
        if stage.stage_id == stage_id:
            return stage
    raise KeyError(f"Unknown stage: {stage_id}")
