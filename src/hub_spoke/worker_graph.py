from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, Iterable, List

WORKER_ALIASES = {
    "history": "history",
    "history-analyzer": "history",
    "news": "news",
    "news-analyzer": "news",
    "market-news-collector": "news",
    "company": "company",
    "company-performance": "company",
    "company-performance-agent": "company",
    "chart": "chart",
    "chart-analyzer": "chart",
    "sentiment": "sentiment",
    "market-sentiment": "sentiment",
    "market-sentiment-analyzer": "sentiment",
    "build": "build",
    "stage-build-sequence": "build",
    "environment": "environment",
    "environment-checks": "environment",
    "paper": "paper",
    "paper-trading": "paper",
    "shadow": "shadow",
    "shadow-mode": "shadow",
    "live": "live",
    "live-mode": "live",
    "observability": "observability",
    "observability-and-logs": "observability",
    "model": "model",
    "model-diversity-checks": "model",
    "fundamental": "fundamental",
    "fundamental-agent": "fundamental",
    "technical": "technical",
    "technical-agent": "technical",
    "risk": "risk",
    "risk-sentiment-agent": "risk",
    "debate": "debate",
    "debate-controller": "debate",
    "master": "master",
    "master-agent": "master",
    "execution": "execution",
    "execution-agent": "execution",
}

WORKER_DEPENDENCY_GRAPH: Dict[str, List[str]] = {
    "news": [],
    "company": [],
    "chart": [],
    "sentiment": [],
    "history": ["news", "chart", "sentiment", "company"],
    "build": ["history"],
    "environment": ["history", "build"],
    "fundamental": ["history"],
    "technical": ["history"],
    "model": ["history"],
    "observability": ["environment", "execution"],
    "risk": ["environment", "fundamental", "technical", "model", "history", "sentiment"],
    "debate": ["risk", "fundamental", "technical"],
    "master": ["debate", "risk"],
    "execution": ["master", "risk", "environment"],
    "paper": ["execution", "risk", "environment"],
    "shadow": ["paper", "execution", "risk"],
    "live": ["shadow", "paper", "execution"],
}

WORKER_STAGE_PRIORITY = {
    "news": 0,
    "chart": 1,
    "sentiment": 2,
    "company": 3,
    "history": 4,
    "fundamental": 5,
    "technical": 4,
    "model": 4,
    "environment": 5,
    "risk": 6,
    "debate": 7,
    "master": 8,
    "execution": 9,
    "paper": 10,
    "shadow": 11,
    "live": 12,
    "observability": 9,
    "build": 5,
}


def normalize_worker_name(name: str) -> str:
    key = str(name).strip().lower()
    return WORKER_ALIASES.get(key, key)


def expand_required_workers(workers: Iterable[str]) -> List[str]:
    expanded: List[str] = []
    seen: set[str] = set()
    stack = [normalize_worker_name(name) for name in workers if name]
    while stack:
        worker = stack.pop()
        if worker in seen:
            continue
        seen.add(worker)
        expanded.append(worker)
        for dep in WORKER_DEPENDENCY_GRAPH.get(worker, []):
            if dep not in seen:
                stack.append(dep)
    return expanded


def resolve_execution_order(workers: Iterable[str]) -> List[str]:
    required = {normalize_worker_name(w) for w in workers if w}
    for worker in list(required):
        for dep in WORKER_DEPENDENCY_GRAPH.get(worker, []):
            required.add(dep)

    indegree: Dict[str, int] = {worker: 0 for worker in required}
    adjacency: Dict[str, List[str]] = defaultdict(list)

    for worker in required:
        for dep in WORKER_DEPENDENCY_GRAPH.get(worker, []):
            if dep in required:
                adjacency[dep].append(worker)
                indegree[worker] += 1

    queue = deque(sorted(worker for worker, degree in indegree.items() if degree == 0))
    ordered: List[str] = []

    while queue:
        current = queue.popleft()
        ordered.append(current)
        for dependent in sorted(adjacency.get(current, [])):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)

    if len(ordered) != len(required):
        remaining = [worker for worker in sorted(required) if worker not in ordered]
        raise ValueError(f"Cyclic dependency detected among workers: {remaining}")

    return ordered


def resolve_parallel_stages(workers: Iterable[str]) -> List[List[str]]:
    required = {normalize_worker_name(w) for w in workers if w}
    for worker in list(required):
        for dep in WORKER_DEPENDENCY_GRAPH.get(worker, []):
            required.add(dep)

    indegree: Dict[str, int] = {worker: 0 for worker in required}
    adjacency: Dict[str, List[str]] = defaultdict(list)

    for worker in required:
        for dep in WORKER_DEPENDENCY_GRAPH.get(worker, []):
            if dep in required:
                adjacency[dep].append(worker)
                indegree[worker] += 1

    ready = deque(
        sorted(
            (worker for worker, degree in indegree.items() if degree == 0),
            key=lambda w: WORKER_STAGE_PRIORITY.get(w, 999),
        )
    )
    stages: List[List[str]] = []

    while ready:
        current_stage = sorted(ready, key=lambda w: WORKER_STAGE_PRIORITY.get(w, 999))
        stages.append(current_stage)
        next_ready: List[str] = []
        for current in current_stage:
            for dependent in sorted(adjacency.get(current, []), key=lambda w: WORKER_STAGE_PRIORITY.get(w, 999)):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    next_ready.append(dependent)
        ready = deque(sorted(set(next_ready), key=lambda w: WORKER_STAGE_PRIORITY.get(w, 999)))

    if sum(len(stage) for stage in stages) != len(required):
        remaining = [worker for worker in sorted(required) if not any(worker in stage for stage in stages)]
        raise ValueError(f"Cyclic dependency detected among workers: {remaining}")

    return stages
