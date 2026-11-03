"""Entry-point based adapter discovery."""
from __future__ import annotations
from importlib.metadata import entry_points
from typing import Any

def discover_adapters() -> dict[str, Any]:
    """Load trusted third-party adapters registered in loop_maker.agents."""
    points = entry_points()
    selected = points.select(group="loop_maker.agents") if hasattr(points, "select") else points.get("loop_maker.agents", [])
    discovered = {}
    for point in selected:
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
