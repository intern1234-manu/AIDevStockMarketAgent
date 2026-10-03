# Task Executor and Agent Flow Guide

This file documents the real runtime behavior of the project as implemented in the codebase. It is intentionally kept inside the knowledge base so the operational model stays organized with the rest of the project memory and learning artifacts.

## 1. Actual code flow

The execution model is made up of the following layers:

1. `main.py` creates or submits the initial `AgentTask`.
2. `HubSpokeOrchestrator.run()` in `src/hub_spoke/orchestrator.py` receives the task and calls the driver.
3. `StockPlannerDriver.classify_task()` in `src/hub_spoke/driver_agent.py` asks the planner for a recommended execution plan.
4. `LLMTaskPlanner.plan_task()` in `src/hub_spoke/planner.py` tries to use an LLM if an API key is configured; otherwise it falls back to heuristic routing.
5. `resolve_execution_order()` and `resolve_parallel_stages()` in `src/hub_spoke/worker_graph.py` normalize worker names and enforce dependencies.
6. `TaskScheduler.decide_mode()` in `src/hub_spoke/task_scheduler.py` decides if the stage should run in parallel or sequentially.
7. `WorkflowEngine.run()` in `src/hub_spoke/workflow.py` only marks tasks as runnable when prerequisites are satisfied.
8. `StockPlannerDriver.execute_parallel()` or `StockPlannerDriver.execute()` then runs the assigned workers.
9. Every worker inherits from `BaseWorkerAgent` and persists queue and memory state under `.worker_state`.
10. Each result is written to execution history and memory, allowing later review and learning.

---

## 2. Driver, planner, orchestrator, and workflow responsibilities

### Driver agent
File: `src/hub_spoke/driver_agent.py`

Purpose:
- central hub that receives tasks
- calls the planner
- resolves execution order
- decides whether to fan out parallel workers or run a strict sequence
- executes each worker and packages the final result

Key logic:
- `StockPlannerDriver.__init__()` creates the worker registry
- `classify_task()` turns a task into a decision and ordered worker list
- `execute_parallel()` fans out independent workers by dependency stage
- `execute()` runs workers in sequence for non-parallel tasks

### Planner
File: `src/hub_spoke/planner.py`

Purpose:
- maps incoming task intent to worker assignments
- decides priority and route state
- uses LLM-first planning if configured, otherwise heuristics
- produces `PlannerDecision` with `assigned_workers`, `execution_order`, `priority`, and `requires_parallel`

Key logic:
- `infer_task_priority()`
- `infer_route_state()`
- `route_for_state()`
- `LLMTaskPlanner.heuristic_plan()`
- `LLMTaskPlanner.build_prompt()`
- `LLMTaskPlanner.plan_task()`

### Orchestrator
File: `src/hub_spoke/orchestrator.py`

Purpose:
- a simple top-level runner that sends tasks through the driver
- can run tasks in sequential or parallel mode at the orchestration layer

Key logic:
- `HubSpokeOrchestrator.run()`
- `HubSpokeOrchestrator.run_many()`

### Workflow engine
File: `src/hub_spoke/workflow.py`

Purpose:
- handles dependency-based readiness
- prevents a task from running until its prerequisites are complete
- decides which queued task is next according to priority and dependency readiness

Key logic:
- `WorkflowEngine.enqueue()`
- `WorkflowEngine.submit()`
- `_ready_tasks()`
- `_resolve_next_task()`
- `run()`

### Queue and scheduler
Files:
- `src/hub_spoke/queue.py`
- `src/hub_spoke/task_scheduler.py`

Purpose:
- hold pending jobs in memory
- apply priority ordering
- choose execution mode
- maintain a reusable scheduling layer for industry-style priority handling

Key logic:
- `TaskQueue.enqueue()`, `dequeue()`, `complete()`, `peek()`
- `TaskScheduler.decide_mode()`
- `TaskScheduler.schedule()`
- `PRIORITY_ORDER` values: `critical`, `high`, `medium`, `normal`, `low`

### Dependency graph
File: `src/hub_spoke/worker_graph.py`

Purpose:
- normalizes names such as `history-analyzer` and `market-news-collector` into canonical worker keys
- defines dependency edges in a graph
- resolves execution order and parallel stages

Key logic:
- `WORKER_ALIASES`
- `WORKER_DEPENDENCY_GRAPH`
- `normalize_worker_name()`
- `expand_required_workers()`
- `resolve_execution_order()`
- `resolve_parallel_stages()`

### Models and contracts
File: `src/hub_spoke/models.py`

Purpose:
- `AgentTask` defines the input structure for each worker task
- `AgentResult` defines the output structure for each worker

Key fields:
- `task_id`, `title`, `description`, `priority`, `state`, `context`, `tags`
- `agent_name`, `status`, `summary`, `details`, `dependencies`

### Roadmap / stage planning
File: `src/hub_spoke/roadmap.py`

Purpose:
- creates the stage-based workflow for a stock-trading rollout
- defines operational phases from infrastructure readiness to paper trading, shadow mode, and live mode

Key logic:
- `WorkflowStage`
- `STOCK_TRADING_ROADMAP`
- `build_stock_trading_queue()`
- `get_stage_by_id()`

---

## 3. Worker model and agent responsibilities

### Shared worker base
File: `src/hub_spoke/workers/base_agent.py`

Purpose:
- shared behavior for every specialized worker
- handles prompt generation, state persistence, queueing, memory writes, and execution history
- ensures workers can survive restarts without losing the latest queue or memory state

Key logic:
- `BaseWorkerAgent.__init__()`
- `persist_state()` / `load_state()`
- `enqueue()`, `dequeue()`, `peek_queue()`
- `write_memory()`, `read_memory()`
- `record_execution()`
- `build_prompt()`
- `execute()`

### Worker set and responsibilities

- `history_analyzer.py` — historical pattern review, regime context, and prior decision-quality analysis.
- `stage_build_sequence.py` — milestone planning and rollout sequencing.
- `environment_checks.py` — environment readiness, dependency checks, runtime validation.
- `paper_trading.py` — low-risk simulation of the order flow.
- `shadow_mode.py` — live-like evaluation without real order submission.
- `live_mode.py` — final production-ready rollout guardrails and execution plan.
- `observability.py` — health monitoring, logs, and operational visibility.
- `model_diversity.py` — model independence and diversity verification.
- `fundamental_agent.py` — business quality, valuation, earnings quality, and strategy review.
- `technical_agent.py` — timing quality and trade signal framing.
- `risk_sentiment_agent.py` — risk gate, volatility review, and safety validation.
- `debate_controller.py` — challenge the thesis and compare argument quality.
- `master_agent.py` — final acceptance, reduction, or veto decision.
- `execution_agent.py` — converts an approved decision into a broker-safe route.
- `market_news_agent.py` — macro and news collection.
- `company_performance_agent.py` — 5-year company profile and strategic performance summary.
- `chart_analyzer.py` — technical chart assessment.
- `market_sentiment_agent.py` — broader market sentiment analysis.

### Worker export file
File: `src/hub_spoke/workers/__init__.py`

Purpose:
- exposes the worker classes to the rest of the project
- keeps the codebase organized and consistent when the driver imports agents

### Aggregated worker registry
File: `src/hub_spoke/worker_agents.py`

Purpose:
- central registry of the reusable worker classes from the workers package
- keeps imports centralized for orchestration and driver setup

---

## 4. Dependency-aware decision flow

The system is intentionally not a flat queue. It uses a dependency graph to decide what is safe to run next.

A typical stage order is:

- news, company, chart, sentiment
- history, fundamental, technical, environment
- risk
- debate
- master
- execution
- paper / shadow
- live

This logic is implemented in `WORKER_DEPENDENCY_GRAPH` inside `src/hub_spoke/worker_graph.py`.

The key policy is:
- research workers can fan out in parallel when independently useful
- approval and execution workers must wait until upstream evidence is complete
- no final decision should be made before risk and debate gates are cleared

---

## 5. Industry-style execution model

The architecture follows a realistic trading workflow:

1. gather evidence
2. validate the company and market backdrop
3. confirm quality through fundamentals and technicals
4. assess risk and sentiment
5. challenge the thesis in a debate stage
6. obtain master approval
7. prepare execution route and risk checks
8. move through paper, shadow, and then live stages

This is the actual design logic encoded into the project to avoid simple queue ordering and to enforce stage readiness based on actual prerequisites.

---

## 6. Operational memory and learning

The knowledge base is intentionally used to retain:
- prompt strategy and agent responsibilities
- audit notes and duplicate-task checks
- learning from mistakes and prompt correction patterns

The worker memory is persisted in JSON under `.worker_state`, while the project-level learning artifacts live under `knowledge-base/`.

This separates runtime state from human-readable knowledge and keeps the system auditable and easier to maintain.

---

## 9. Operational guidance

Use this guide when you want to understand:

- what each worker does
- why tasks are scheduled in a certain order
- why some stages run in parallel and others run sequentially
- how the architecture supports safer decision making instead of raw queue ordering

This is the project’s actual execution model: not just a list of agents, but a dependency-aware trading and research workflow.
