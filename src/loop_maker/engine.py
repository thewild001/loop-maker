"""Bounded orchestration loop with injectable agent, evaluator and persistence."""
from __future__ import annotations

import asyncio
import uuid
from typing import Any

from .contracts import (
    AgentAdapter,
    AgentResult,
    EvaluationResult,
    Evaluator,
    LoopConfig,
    LoopResult,
    Task,
)
from .storage import SessionStore


class EvaluationFailure(RuntimeError):
    """The evaluator is missing, invalid, or failed to provide a trustworthy result."""


class LoopEngine:
    def __init__(self, store: SessionStore | None = None,
                 evaluator: Evaluator | None = None) -> None:
        self.store = store or SessionStore(":memory:")
        self.evaluator = evaluator

    async def run(self, agent: AgentAdapter, task: Task,
                  config: LoopConfig | None = None) -> LoopResult:
        config = config or LoopConfig()
        if not 1 <= config.max_iterations <= 20:
            raise ValueError("max_iterations must be between 1 and the hard safety limit of 20")
        if config.min_output_chars < 0:
            raise ValueError("min_output_chars must not be negative")
        if config.mode not in {"BASIC", "DETAIL", "FORCED_DETAIL", "MINIMAL"}:
            raise ValueError("unsupported execution mode")
        if not task.objective.strip():
            raise ValueError("objective must not be empty")
        if not task.domain.strip():
            raise ValueError("task domain must not be empty")

        session_id = config.session_id or str(uuid.uuid4())
        self.store.start_session(session_id, agent.agent_id, task.objective, config.mode)
        context: dict[str, Any] = {
            "session_id": session_id, "mode": config.mode, "domain": task.domain,
            "acceptance_criteria": task.acceptance_criteria,
            "constraints": task.constraints, "iteration": 0, "previous_feedback": None,
        }
        errors: list[dict[str, str]] = []
        last_output = ""
        status, converged = "FAILED", False
        iteration = 0

        for iteration in range(1, config.max_iterations + 1):
            context["iteration"] = iteration
            try:
                result = await asyncio.wait_for(
                    agent.execute(task, context),
                    timeout=float(task.metadata.get("timeout_seconds", 900)),
                )
                if not isinstance(result, AgentResult):
                    raise TypeError("AgentAdapter.execute() must return AgentResult")
                last_output = result.output or ""
                try:
                    evaluation = await asyncio.wait_for(
                        self._evaluate(task, result, config),
                        timeout=float(task.metadata.get("evaluation_timeout_seconds", 120)),
                    )
                except TimeoutError as exc:
                    raise EvaluationFailure("Evaluator timed out") from exc
                self.store.record_iteration(
                    session_id, iteration, last_output, evaluation["accepted"],
                    result.usage, {**result.metadata, "evaluation": evaluation,
                                   "domain": task.domain},
                )
                if evaluation["accepted"]:
                    status, converged = "COMPLETED", True
                    break
                status = "MAX_ITERATIONS"
                context["previous_feedback"] = (
                    result.feedback or evaluation["reason"]
                    or "Improve the result against the original acceptance criteria."
                )
            except asyncio.CancelledError:
                self.store.finish_session(session_id, "CANCELLED", False, last_output)
                raise
            except EvaluationFailure as exc:
                errors.append({"code": "H", "message": str(exc)})
                self.store.record_error(session_id, iteration, "H", str(exc))
                status = "FAILED"
                break
            except TimeoutError:
                errors.append({"code": "F", "message": "Agent execution timed out"})
                self.store.record_error(session_id, iteration, "F", errors[-1]["message"])
                status = "CIRCUIT_BROKEN"
                break
            except Exception as exc:  # noqa: BLE001 - normalize arbitrary adapter failures at the boundary
                errors.append({"code": "D", "message": f"{type(exc).__name__}: {exc}"})
                self.store.record_error(session_id, iteration, "D", errors[-1]["message"])
                status = "FAILED"
                break

        if not converged and status == "MAX_ITERATIONS":
            message = "Acceptance was not reached within the iteration budget"
            errors.append({"code": "B", "message": message})
            self.store.record_error(session_id, iteration, "B", message)
            status = "CIRCUIT_BROKEN"
        self.store.finish_session(session_id, status, converged, last_output)
        return LoopResult(session_id, status, converged, iteration, last_output,
                          errors, {"agent_id": agent.agent_id, "mode": config.mode,
                                   "domain": task.domain})

    async def _evaluate(self, task: Task, result: AgentResult,
                        config: LoopConfig) -> dict[str, Any]:
        if not result.success:
            return {"accepted": False, "reason": result.feedback or "Agent reported failure"}
        if not result.complete:
            return {"accepted": False, "reason": result.feedback or "Agent reports incomplete work"}
        if len(result.output.strip()) < config.min_output_chars:
            return {"accepted": False, "reason": "Output is empty or below the configured minimum"}

        # A configured evaluator is always invoked: it may enforce domain-specific quality
        # gates even when the user did not provide explicit acceptance criteria.
        if self.evaluator is None:
            if task.acceptance_criteria:
                raise EvaluationFailure(
                    "Mandatory criteria exist but no independent evaluator is configured"
                )
            return {"accepted": True, "reason": "Agent completed; no domain evaluator configured"}

        try:
            evaluation: EvaluationResult = await self.evaluator.evaluate(task, result)
        except Exception as exc:
            raise EvaluationFailure(f"Evaluator failed: {type(exc).__name__}: {exc}") from exc
        if not isinstance(evaluation, EvaluationResult):
            raise EvaluationFailure("Evaluator must return EvaluationResult")
        if (
            not isinstance(evaluation.verified_criteria, list)
            or not isinstance(evaluation.failed_criteria, list)
            or not isinstance(evaluation.evidence, dict)
            or any(
                not isinstance(key, str) or not isinstance(value, str)
                for key, value in evaluation.evidence.items()
            )
            or any(not isinstance(item, str) for item in
                   evaluation.verified_criteria + evaluation.failed_criteria)
        ):
            raise EvaluationFailure("Evaluator returned an invalid evidence structure")

        required = set(task.acceptance_criteria)
        verified = set(evaluation.verified_criteria)
        failed = set(evaluation.failed_criteria)
        if required:
            missing = required - verified
            evidence_missing = required - set(evaluation.evidence)
            accepted = not failed and not missing and not evidence_missing and all(
                evaluation.evidence[item].strip() for item in required
            )
            reason = "All mandatory criteria verified" if accepted else (
                "Acceptance criteria lack complete independent evidence"
            )
        else:
            accepted = evaluation.accepted is True and bool(evaluation.evidence) and all(
                value.strip() for value in evaluation.evidence.values()
            ) and not failed
            reason = "Domain evaluator accepted the result" if accepted else (
                "Domain evaluator did not provide explicit acceptance with evidence"
            )
        return {
            "accepted": accepted,
            "reason": evaluation.feedback or reason,
            "verified_criteria": evaluation.verified_criteria,
            "failed_criteria": evaluation.failed_criteria,
            "evidence": evaluation.evidence,
        }
