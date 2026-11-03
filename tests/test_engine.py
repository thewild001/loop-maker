import asyncio
import pytest

from loop_maker.contracts import AgentResult, LoopConfig, Task
from loop_maker.engine import LoopEngine

class CompletingAgent:
    agent_id = "test-agent"
    def capabilities(self):
        return {"execute": True}
    async def execute(self, task, context):
        return AgentResult(output="done", complete=True)

class NeverCompletesAgent:
    agent_id = "never-completes"
    def capabilities(self):
        return {"execute": True}
    async def execute(self, task, context):
        return AgentResult(output="work in progress", complete=False, feedback="continue")

@pytest.mark.asyncio
async def test_converges_when_agent_returns_complete_result():
    result = await LoopEngine().run(CompletingAgent(), Task("test"))
    assert result.converged is True
    assert result.status == "COMPLETED"
    assert result.iterations == 1

@pytest.mark.asyncio
async def test_stops_at_iteration_budget():
    result = await LoopEngine().run(
        NeverCompletesAgent(), Task("test"), LoopConfig(max_iterations=2)
    )
    assert result.converged is False
    assert result.status == "CIRCUIT_BROKEN"
    assert result.iterations == 2

def test_rejects_zero_iteration_budget():
    with pytest.raises(ValueError):
        asyncio.run(LoopEngine().run(
            CompletingAgent(), Task("test"), LoopConfig(max_iterations=0)
        ))
