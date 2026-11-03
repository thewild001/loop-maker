---
name: loop-maker-orchestrator
description: Orchestrate bounded, measurable improvement loops for any AI-agent task, including research, analysis, writing, planning, software, data, operations and creative workflows.
---

# Loop Maker Orchestrator

Loop Maker is a general-purpose orchestration layer. The connected agent remains responsible for carrying out the work with its own model, tools, connectors, memory and runtime. Never assume that the task is software development.

## Task lifecycle

1. Understand the requested outcome, domain, audience, constraints, format and authorization.
2. Select BASIC, DETAIL, FORCED_DETAIL or MINIMAL mode.
3. Define mandatory acceptance criteria and optional preferences using a domain-appropriate rubric.
4. If Loop Maker MCP is available, start or recover a session and retain its identifier.
5. Execute one bounded work unit with the connected agent's native capabilities.
6. Evaluate the result against evidence appropriate to the domain.
7. Record the iteration, findings and only those usage metrics actually exposed by the host.
8. If criteria fail, classify the cause and choose a materially different recovery strategy.
9. Converge only when mandatory criteria pass and no critical error remains.
10. Stop at the iteration, time, resource or safety budget.
11. Finish the session and report evidence, unresolved issues and limitations.

## Domain-aware evaluation

- Research: relevance, source authority, recency, corroboration, coverage and uncertainty.
- Analysis: sound assumptions, reproducible reasoning, correct calculations and alternatives.
- Writing: factual integrity, audience fit, completeness, tone, structure and requested format.
- Planning: feasibility, dependencies, risks, sequencing, ownership and measurable milestones.
- Software: behavior, tests, security, compatibility and maintainability.
- Data: provenance, data quality, transformations, statistical validity and reproducibility.
- Operations: authorization, reversibility, blast radius, auditability and verified outcome.
- Creative work: brief alignment, internal coherence, constraints and user feedback.

Do not apply a coding test rubric to research or a citation requirement to a purely creative task unless the user asks for it. When criteria cannot be evaluated reliably, mark them unverified instead of inventing confidence.

## Error taxonomy

- A: invalid, missing or contradictory input — clarify.
- B: ineffective technique — change strategy.
- C: invalid output structure — repair against the contract.
- D: agent, provider, tool or source failure — diagnose the boundary.
- E: inconsistent state or conflicting evidence — reconcile or restore.
- F: resource exhaustion or timeout — reduce scope once, then stop.
- G: context truncation — compact or modularize.
- H: unreliable evaluation — require independent or stronger evidence.
- I: security, privacy, authorization or policy violation — stop immediately.

## Convergence and reporting

Iteration count is not progress. Do not fabricate token counts, latency, scores, citations or evidence. Mandatory criteria cannot be averaged away by a quality score.

Return status (CONVERGED / PARTIAL / FAILED / CIRCUIT_BROKEN), task domain, mode, iterations, criteria passed/failed/unverified, evidence, recovery actions, measured usage only when supplied by the host, and remaining risks.
