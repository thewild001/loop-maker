"""Optional MCP server exposing Loop Maker operations."""
from __future__ import annotations
import os
try:
    from mcp.server import MCPServer
except ImportError as exc:
    raise SystemExit('Install MCP support with: pip install "loop-maker-orchestrator[mcp]"') from exc

from .contracts import LoopConfig, Task
from .demo_agent import DemoAgent
from .engine import LoopEngine
from .registry import discover_adapters
from .storage import SessionStore

mcp = MCPServer("loop-maker-orchestrator")
store = SessionStore(os.getenv("LOOP_MAKER_DB", "loop-maker.sqlite3"))
engine = LoopEngine(store)
agents = {"demo": DemoAgent(), **discover_adapters()}
VALID_MODES = {"BASIC", "DETAIL", "FORCED_DETAIL", "MINIMAL"}

@mcp.tool()
def loop_list_agents() -> list[dict]:
    """List registered agent adapters and their declared capabilities."""
    return [{"agent_id": key, "capabilities": adapter.capabilities()}
            for key, adapter in sorted(agents.items())]

@mcp.tool()
async def loop_run(objective: str, agent_id: str = "demo",
                   max_iterations: int = 3, mode: str = "BASIC",
                   acceptance_criteria: list[str] | None = None,
                   constraints: list[str] | None = None) -> dict:
    """Run an objective through a registered agent adapter.

    The demo adapter validates the MCP path only. Install a trusted adapter
    plugin to execute real work through a coding or task agent.
    """
    if agent_id not in agents:
        return {"error": "unknown_agent", "available_agents": sorted(agents)}
    if mode not in VALID_MODES:
        return {"error": "invalid_mode", "valid_modes": sorted(VALID_MODES)}
    result = await engine.run(
        agents[agent_id],
        Task(objective=objective, acceptance_criteria=acceptance_criteria or [],
             constraints=constraints or []),
        LoopConfig(max_iterations=max_iterations, mode=mode),
    )
    return {"session_id": result.session_id, "agent_id": agent_id,
            "status": result.status, "converged": result.converged,
            "iterations": result.iterations, "output": result.output,
            "errors": result.errors, "metrics": result.metrics}

@mcp.tool()
def loop_get_session(session_id: str) -> dict:
    """Retrieve a persisted Loop Maker session by identifier."""
    return store.get_session(session_id) or {"error": "session_not_found"}

def main() -> None:
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
