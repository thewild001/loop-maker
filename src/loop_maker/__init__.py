"""Agent-agnostic orchestration engine."""
from .contracts import AgentAdapter, AgentResult, LoopConfig, LoopResult, Task
from .engine import LoopEngine

__all__ = ["AgentAdapter", "AgentResult", "LoopConfig", "LoopEngine", "LoopResult", "Task"]
__version__ = "0.1.0"
