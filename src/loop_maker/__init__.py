"""Agent-agnostic orchestration engine."""
from .contracts import (
    AgentAdapter,
    AgentResult,
    EvaluationResult,
    Evaluator,
    LoopConfig,
    LoopResult,
    Task,
)

from .engine import LoopEngine

__all__ = [
    "AgentAdapter", "AgentResult", "EvaluationResult", "Evaluator",
    "LoopConfig", "LoopEngine", "LoopResult", "Task",
]
__version__ = "0.1.0"
