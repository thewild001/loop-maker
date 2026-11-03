---
name: loop-maker-stress-test
description: Stress-test an iterative workflow, plan, analysis, content artifact, data process, software system or agent loop against edge cases and failure modes.
---

# STRESS-TEST

Design adversarial and boundary scenarios that are relevant to the target domain. Do not assume the target is code.

Possible dimensions:
- Ambiguous, incomplete or contradictory requirements.
- Missing, stale, biased or conflicting evidence.
- Invalid assumptions, extreme values or calculation boundaries.
- Format, schema, audience or accessibility constraints.
- Dependency failure, interrupted execution or unavailable tools.
- Context loss, repeated failure, evaluator disagreement and resource exhaustion.
- Privacy, authorization, security and unsafe side effects.
- Unexpected user feedback or changed objectives.

For each scenario specify setup/input, risk being tested, expected behavior, evidence required to pass, maximum retries, and recovery expectations.

Use isolated fixtures, synthetic data or non-production environments when applicable. Never run destructive or externally visible tests without explicit authorization. Report coverage gaps; a test plan is not proof that tests were executed.
