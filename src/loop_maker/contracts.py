"""Stable, framework-neutral contracts used by the Loop Maker core."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Protocol

@dataclass(slots=True)
class Task:
    objective: str
    acceptance_criteria: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(slots=True)
class AgentResult:
    """Normalized result returned by an agent adapter."""
    output: str
    success: bool = True
    complete: bool = True
    feedback: str | None = None
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(slots=True)
class EvaluationResult:
    """Evidence-backed evaluation of mandatory acceptance criteria."""
    verified_criteria: list[str] = field(default_factory=list)
    failed_criteria: list[str] = field(default_factory=list)
    evidence: dict[str, str] = field(default_factory=dict)
    feedback: str | None = None

@dataclass(slots=True)
class LoopConfig:
    max_iterations: int = 3
    mode: str = "BASIC"
    min_output_chars: int = 1
    session_id: str | None = None

@dataclass(slots=True)
class LoopResult:
    session_id: str
    status: str
    converged: bool
    iterations: int
    output: str
    errors: list[dict[str, str]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

class AgentAdapter(Protocol):
    @property
    def agent_id(self) -> str: ...
    async def execute(self, task: Task, context: dict[str, Any]) -> AgentResult:
        """Execute one bounded work unit and return a normalized result."""
        ...
    def capabilities(self) -> dict[str, Any]:
        """Describe optional features; never claim unsupported capabilities."""
        ...

class Evaluator(Protocol):
    async def evaluate(self, task: Task, result: AgentResult) -> EvaluationResult:
        """Verify criteria and return evidence; do not rely on agent confidence."""
        ...
