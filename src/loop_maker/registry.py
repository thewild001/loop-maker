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
        if not hasattr(adapter, "execute") or not hasattr(adapter, "capabilities"):
            raise TypeError(f"Adapter '{point.name}' does not implement the Loop Maker contract")
        discovered[point.name] = adapter
    return discovered
