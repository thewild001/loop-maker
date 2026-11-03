"""Command-line entry point."""
from __future__ import annotations
import argparse
import asyncio
import json
from .contracts import LoopConfig, Task
from .demo_agent import DemoAgent
from .engine import LoopEngine
from .registry import discover_adapters, discover_evaluator
from .storage import SessionStore

def main() -> None:
    parser = argparse.ArgumentParser(prog="loop-maker", description="Agent-agnostic iteration orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run an objective through an installed agent adapter")
    run.add_argument("objective")
    run.add_argument("--agent", default="demo")
    run.add_argument("--max-iterations", type=int, default=3)
    run.add_argument("--mode", default="BASIC",
                     choices=["BASIC", "DETAIL", "FORCED_DETAIL", "MINIMAL"])
    run.add_argument("--db", default="loop-maker.sqlite3")
    args = parser.parse_args()
    adapters = {"demo": DemoAgent(), **discover_adapters()}
    if args.agent not in adapters:
        parser.error(f"Unknown agent '{args.agent}'. Installed adapters: {', '.join(sorted(adapters))}")
    engine = LoopEngine(SessionStore(args.db), evaluator=discover_evaluator())
    result = asyncio.run(engine.run(adapters[args.agent], Task(objective=args.objective),
        LoopConfig(max_iterations=args.max_iterations, mode=args.mode)))
    print(json.dumps({
        "session_id": result.session_id, "status": result.status,
        "converged": result.converged, "iterations": result.iterations,
        "output": result.output, "errors": result.errors, "metrics": result.metrics,
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
