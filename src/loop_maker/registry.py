"""Entry-point based discovery for trusted agent adapters and evaluators."""
from __future__ import annotations

from importlib.metadata import entry_points
from typing import Any

def _select(group: str):
    points = entry_points()
    return points.select(group=group) if hasattr(points, "select") else points.get(group, [])

def discover_adapters() -> dict[str, Any]:
    """Load trusted third-party adapters registered in loop_maker.agents."""
    discovered = {}
    for point in _select("loop_maker.agents"):
        factory = point.load()
        adapter = factory()
        if not callable(getattr(adapter, "execute", None)):
            raise TypeError(f"Adapter '{point.name}' must implement async execute(task, context)")
        if not callable(getattr(adapter, "capabilities", None)):
            raise TypeError(f"Adapter '{point.name}' must implement capabilities()")
        if not isinstance(getattr(adapter, "agent_id", None), str) or not adapter.agent_id.strip():
            raise TypeError(f"Adapter '{point.name}' must expose a non-empty agent_id")
        if not isinstance(adapter.capabilities(), dict):
            raise TypeError(f"Adapter '{point.name}' capabilities() must return a dictionary")
        discovered[point.name] = adapter
    return discovered

def discover_evaluator() -> Any | None:
    """Load the single default evaluator plugin, if one is installed."""
    points = list(_select("loop_maker.evaluators"))
    if not points:
        return None
    if len(points) > 1:
        raise RuntimeError(
            "Multiple evaluator plugins found; configure one default evaluator before startup"
        )
    evaluator = points[0].load()()
    if not callable(getattr(evaluator, "evaluate", None)):
        raise TypeError("Evaluator plugin must implement async evaluate(task, result)")
    return evaluator
