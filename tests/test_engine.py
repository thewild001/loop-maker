import asyncio

import pytest

from loop_maker.contracts import (
    AgentResult,
    EvaluationResult,
    LoopConfig,
    Task,
)
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

class EvidenceEvaluator:
    async def evaluate(self, task, result):
        return EvaluationResult(
            verified_criteria=list(task.acceptance_criteria),
            evidence={"tests pass": "pytest -q: all tests passed"},
        )

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

@pytest.mark.asyncio
async def test_mandatory_criteria_need_independent_evaluator():
    result = await LoopEngine().run(
        CompletingAgent(), Task("test", acceptance_criteria=["tests pass"])
    )
    assert result.status == "FAILED"
    assert result.errors[0]["code"] == "H"
    assert result.converged is False

@pytest.mark.asyncio
async def test_evaluator_must_verify_all_mandatory_criteria():
    result = await LoopEngine(evaluator=EvidenceEvaluator()).run(
        CompletingAgent(), Task("test", acceptance_criteria=["tests pass"])
    )
    assert result.status == "COMPLETED"
    assert result.converged is True

def test_rejects_zero_iteration_budget():
    with pytest.raises(ValueError):
        asyncio.run(LoopEngine().run(
            CompletingAgent(), Task("test"), LoopConfig(max_iterations=0)
        ))

@pytest.mark.asyncio
async def test_cancelled_execution_is_persisted_as_terminal_state():
    from loop_maker.storage import SessionStore
    store = SessionStore(":memory:")
    class BlockingAgent:
        agent_id = "blocking-agent"

        def capabilities(self):
            return {"execute": True}

        async def execute(self, task, context):
            await asyncio.Event().wait()

    engine = LoopEngine(store)
    running = asyncio.create_task(engine.run(
        BlockingAgent(), Task("cancel me"),
        LoopConfig(session_id="cancel-session", max_iterations=5),
    ))
    await asyncio.sleep(0)
    running.cancel()
    with pytest.raises(asyncio.CancelledError):
        await running
    assert store.get_session("cancel-session")["status"] == "CANCELLED"
