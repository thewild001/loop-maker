---
name: loop-maker-diagnostics
description: Diagnose ineffective loops, non-convergence, agent failures, context limits, and resource exhaustion.
---

# Loop Maker Diagnostics

Classify the observed failure before changing the workflow.

- Input/goal ambiguity: clarify instead of guessing.
- Quality stagnation: compare failed criteria and change strategy.
- Format/schema failure: validate and repair only the invalid structure.
- Adapter/provider failure: inspect connection, runtime, permissions, and capabilities.
- State conflict: restore a known consistent checkpoint.
- Resource failure: reduce task size/context once; stop if it recurs.
- Context truncation: split work into independently verifiable modules.
- Evaluator inconsistency: add deterministic checks or request independent review.
- Security issue: stop and preserve evidence safely.

Record the observed signal, suspected cause, action taken, and verification result. Distinguish facts from hypotheses.
