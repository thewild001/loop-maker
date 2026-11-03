"""Optional MCP server exposing Loop Maker tools, resources and prompts."""
from __future__ import annotations
import os
import uuid
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
VALID_STATUSES = {"COMPLETED", "PARTIAL", "FAILED", "CIRCUIT_BROKEN", "CANCELLED"}

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
    plugin to execute real work through an external agent.
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
def loop_session_start(agent_id: str, objective: str, mode: str = "BASIC") -> dict:
    """Start a durable journal for work performed by the connected host agent."""
    if mode not in VALID_MODES:
        return {"error": "invalid_mode", "valid_modes": sorted(VALID_MODES)}
    session_id = str(uuid.uuid4())
    store.start_session(session_id, agent_id, objective, mode)
    return {"session_id": session_id, "status": "RUNNING"}

@mcp.tool()
def loop_record_iteration(session_id: str, iteration: int, output: str,
                          accepted: bool, usage: dict | None = None,
                          metadata: dict | None = None) -> dict:
    """Persist an iteration completed by the connected host agent."""
    try:
        store.record_iteration(session_id, iteration, output, accepted, usage, metadata)
    except (KeyError, ValueError) as exc:
        return {"error": str(exc)}
    return {"recorded": True, "session_id": session_id, "iteration": iteration}

@mcp.tool()
def loop_record_error(session_id: str, iteration: int, code: str, message: str) -> dict:
    """Persist a classified error and its observed message."""
    if code not in set("ABCDEFGHI"):
        return {"error": "invalid_error_code"}
    store.record_error(session_id, iteration, code, message)
    return {"recorded": True, "session_id": session_id}

@mcp.tool()
def loop_session_finish(session_id: str, status: str, converged: bool,
                        final_output: str) -> dict:
    """Close a host-managed session and persist its final outcome."""
    if status not in VALID_STATUSES:
        return {"error": "invalid_status", "valid_statuses": sorted(VALID_STATUSES)}
    store.finish_session(session_id, status, converged, final_output)
    return {"finished": True, "session_id": session_id, "status": status}

@mcp.tool()
def loop_get_session(session_id: str) -> dict:
    """Retrieve a persisted session, including its iterations and errors."""
    return store.get_session(session_id) or {"error": "session_not_found"}

@mcp.resource("loop-maker://agents")
def agents_catalog() -> str:
    """Current registered agent adapters and capabilities."""
    import json
    return json.dumps([{"agent_id": key, "capabilities": value.capabilities()}
                       for key, value in sorted(agents.items())], ensure_ascii=False)

@mcp.prompt()
def loop_execution_brief(objective: str, mode: str = "BASIC") -> str:
    """Prepare a bounded execution brief for the connected agent."""
    return (
        "Apply the Loop Maker Orchestrator skill.\n"
        f"Objective: {objective}\nMode: {mode}\n"
        "Define mandatory acceptance criteria, execute bounded work units, "
        "validate evidence, record iterations, and stop on safety or resource limits."
    )

def main() -> None:
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
