"""Optional MCP server exposing Loop Maker operations."""
from __future__ import annotations
try:
    from mcp.server import MCPServer
except ImportError as exc:
    raise SystemExit('Install MCP support with: pip install "loop-maker-orchestrator[mcp]"') from exc

from .contracts import LoopConfig, Task
from .demo_agent import DemoAgent
from .engine import LoopEngine

mcp = MCPServer("loop-maker-orchestrator")
engine = LoopEngine()

@mcp.tool()
async def loop_run(objective: str, max_iterations: int = 3, mode: str = "BASIC") -> dict:
    """Run an objective with the built-in demo adapter.

    The demo adapter validates the tool path only. Production deployments must
    register trusted real agent adapters and explicitly allow their use.
    """
    result = await engine.run(DemoAgent(), Task(objective=objective),
                              LoopConfig(max_iterations=max_iterations, mode=mode))
    return {"session_id": result.session_id, "status": result.status,
            "converged": result.converged, "iterations": result.iterations,
            "output": result.output, "errors": result.errors}

@mcp.tool()
def loop_get_session(session_id: str) -> dict:
    """Retrieve a persisted Loop Maker session by identifier."""
    return engine.store.get_session(session_id) or {"error": "session_not_found"}

def main() -> None:
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
