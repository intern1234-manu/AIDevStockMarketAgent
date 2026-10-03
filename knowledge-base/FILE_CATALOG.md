# Python File Catalog and Purpose Map

This catalog describes the actual purpose of the main Python files used by the hub-and-spoke agent system.

## Core orchestration files

### src/hub_spoke/driver_agent.py
Purpose:
- central driver for task delegation
- chooses the worker set and order
- decides parallel vs sequential execution
- runs workers and records results

Key classes:
- `StockPlannerDriver`

Key methods:
- `resolve_execution_order()`
- `classify_task()`
- `classify_task_with_priority()`
- `execute_parallel()`
- `execute()`

### src/hub_spoke/planner.py
Purpose:
- task planning layer for the STD-like driver
- determines which workers are required
- calculates task priority and state route
- chooses heuristic routing when the model is unavailable

Key classes:
- `PlannerDecision`
- `LLMTaskPlanner`

Key functions:
- `infer_task_priority()`
- `infer_route_state()`
- `route_for_state()`
- `LLMTaskPlanner.heuristic_plan()`
- `LLMTaskPlanner.plan_task()`

### src/hub_spoke/orchestrator.py
Purpose:
- top-level entry for orchestrating tasks through the driver
- provides a simpler user-facing execution runner

Key classes:
- `HubSpokeOrchestrator`

Key methods:
- `run()`
- `run_many()`

### src/hub_spoke/workflow.py
Purpose:
- executes tasks only when dependencies are ready
- acts as the dependency-aware workflow engine

Key classes:
- `WorkflowResult`
- `WorkflowEngine`

Key methods:
- `enqueue()`
- `submit()`
- `_ready_tasks()`
- `_resolve_next_task()`
- `run()`

### src/hub_spoke/task_scheduler.py
Purpose:
- decides priority level and run style for tasks
- supports industry-style priority ranking and mode decisions

Key classes:
- `ScheduledTask`
- `TaskScheduler`

Key logic:
- `PRIORITY_ORDER`
- `normalize_priority()`
- `decide_mode()`
- `schedule()`

### src/hub_spoke/queue.py
Purpose:
- in-memory queue for tasks awaiting execution
- records completed tasks for auditability

Key classes:
- `QueueTask`
- `TaskQueue`

### src/hub_spoke/worker_graph.py
Purpose:
- resolves dependency order between workers
- groups independent workers into parallel stages
- normalizes worker aliases to canonical names

Key logic:
- `WORKER_ALIASES`
- `WORKER_DEPENDENCY_GRAPH`
- `resolve_execution_order()`
- `resolve_parallel_stages()`

### src/hub_spoke/models.py
Purpose:
- shared data contracts for the whole project
- input and output schemas for tasks and results

Key dataclasses:
- `AgentTask`
- `AgentResult`

### src/hub_spoke/roadmap.py
Purpose:
- defines the multi-stage stock trading rollout roadmap
- maps the project strategy into stage execution with dependencies

Key classes:
- `WorkflowStage`

Key functions:
- `build_stock_trading_queue()`
- `get_stage_by_id()`

### src/hub_spoke/worker_agents.py
Purpose:
- aggregates the worker classes from the workers package
- acts as a convenient import surface for the driver and orchestrator

### src/hub_spoke/workers/__init__.py
Purpose:
- exposes all worker classes through one package namespace
- central import point for the worker registry

---

## Shared worker base and agent memory

### src/hub_spoke/workers/base_agent.py
Purpose:
- base implementation for all workers
- persists memory and execution history to disk
- stores task queue and last results for recovery

Key features:
- `WORKER_PROMPTS`
- `WORKER_PRIORITY_STANDARDS`
- `persist_state()`, `load_state()`
- `write_memory()`, `read_memory()`
- `record_execution()`
- `build_prompt()`

---

## Specialist worker files

### src/hub_spoke/workers/market_news_agent.py
Purpose:
- collects market news and macro factors
- gathers external context and catalyst information

### src/hub_spoke/workers/company_performance_agent.py
Purpose:
- builds a company-level 5-year performance overview
- reviews market, strategy, and business posture without being tied to one stock name

### src/hub_spoke/workers/chart_analyzer.py
Purpose:
- reviews price structure, momentum, support/resistance, and chart context

### src/hub_spoke/workers/market_sentiment_agent.py
Purpose:
- reviews market mood, sector behavior, and broad sentiment conditions

### src/hub_spoke/workers/history_analyzer.py
Purpose:
- checks historical patterns, previous regime behavior, and relevant prior output

### src/hub_spoke/workers/fundamental_agent.py
Purpose:
- evaluates valuation, earnings quality, business quality, and strategic durability

### src/hub_spoke/workers/technical_agent.py
Purpose:
- interprets technical timing, signal quality, and trade setup strength

### src/hub_spoke/workers/environment_checks.py
Purpose:
- validates runtime requirements, configuration, and operational readiness

### src/hub_spoke/workers/risk_sentiment_agent.py
Purpose:
- evaluates risk posture and safety before approval or execution

### src/hub_spoke/workers/debate_controller.py
Purpose:
- frames opposing views and compares arguments
- improves decision quality before final approval

### src/hub_spoke/workers/master_agent.py
Purpose:
- final decision stage for approval, reduction, or veto

### src/hub_spoke/workers/execution_agent.py
Purpose:
- turns an approved decision into an execution and risk plan

### src/hub_spoke/workers/paper_trading.py
Purpose:
- validates strategy logic in a simulated low-risk environment

### src/hub_spoke/workers/shadow_mode.py
Purpose:
- tests strategy behavior in a live-like mode without real order execution

### src/hub_spoke/workers/live_mode.py
Purpose:
- final production-ready execution and rollout safety layer

### src/hub_spoke/workers/observability.py
Purpose:
- monitors health, logs, alerts, and operational clarity

### src/hub_spoke/workers/model_diversity.py
Purpose:
- checks whether model usage and reasoning steps are sufficiently independent

### src/hub_spoke/workers/stage_build_sequence.py
Purpose:
- converts a task into milestone-based sequencing and stage-based rollout logic

---

## Summary

Each Python file in this project has a distinct role:
- orchestration files manage the flow
- the planner decides intent to workers
- the worker graph enforces ordering and dependency safety
- the workers act as specialist analysis, risk, and execution agents
- the base agent class provides memory, prompts, and persistence across restarts

This is how the driver, planner, orchestrator, and all specialist agents work together as a coordinated multi-agent system.
