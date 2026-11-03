"""Deterministic demo adapter; it proves the contract and is not an LLM agent."""

from .contracts import AgentResult, Task

class DemoAgent:
    @property
    def agent_id(self) -> str:
        return "demo"

    def capabilities(self) -> dict[str, object]:
        return {"execute": True, "streaming": False, "cancellation": False, "artifacts": False}

    async def execute(self, task: Task, context: dict[str, object]) -> AgentResult:
        iteration = int(context["iteration"])
        feedback = context.get("previous_feedback")
        output = (f"[DEMO ONLY] Objective received: {task.objective}\n"
                  f"Iteration: {iteration}\n"
                  "This adapter proves the integration contract; replace it with a real agent adapter.")
        if feedback:
            output += f"\nPrevious feedback: {feedback}"
        return AgentResult(output=output, success=True, complete=True, metadata={"demo": True})
