from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentTask:
    task_id: str
    title: str
    description: str
    priority: str = "normal"
    state: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class AgentResult:
    agent_name: str
    status: str
    summary: str
    task_id: str
    details: Dict[str, Any] = field(default_factory=dict)
    dependencies: Optional[List[str]] = None
