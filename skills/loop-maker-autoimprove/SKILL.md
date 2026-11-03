---
name: loop-maker-autoimprove
description: Propose and validate improvements to an existing loop, agent workflow, or Loop Maker configuration.
---

# AUTOIMPROVE

Do not rewrite a loop merely to make it longer or more sophisticated.

1. Inspect the current loop and its actual execution evidence.
2. Identify the three highest-impact defects or bottlenecks.
3. Classify each issue as Core, Adapter, Agent, Provider, Task, Evaluator, or Environment.
4. Propose the smallest change that addresses the cause.
5. Preserve existing behavior unless a change is justified.
6. Add or update regression cases before accepting the change.
7. Compare quality, completion rate, latency, and resource usage where measurable.
8. Reject changes that improve one metric by violating mandatory criteria.
9. Present a diff and rationale; require approval before publishing or deploying.

Supported focus modifiers: tokens, clarity, quality, Q4, hardware, agent, regression.
