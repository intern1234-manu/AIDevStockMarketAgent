from __future__ import annotations

import json

from src.hub_spoke.models import AgentTask
from src.hub_spoke.roadmap import build_stock_trading_queue
from src.hub_spoke.workflow import WorkflowEngine


def demo() -> None:
    queue_tasks = build_stock_trading_queue()
    workflow = WorkflowEngine()

    for item in queue_tasks:
        workflow.submit(
            AgentTask(
                task_id=item.task_id,
                title=item.title,
                description=item.description,
                priority=item.priority,
                tags=item.workers,
                context={"stage_id": item.task_id, "parallel_allowed": item.metadata.get("parallel_allowed", False)},
            ),
            dependencies=item.dependencies,
        )

    results = workflow.run(mode="sequential")
    print(json.dumps({"workflow_stage_count": len(results), "results": results}, indent=2))


if __name__ == "__main__":
    demo()
