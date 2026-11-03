---
name: loop-maker
description: Apply Loop Maker's bounded iteration method to a task using the current agent's native capabilities.
---

# Loop Maker

Use this skill when the host has no Loop Maker MCP server available. The current agent executes the task; this skill provides the process.

1. Restate the objective internally and identify constraints.
2. Ask one focused clarification if a missing fact changes the solution.
3. Define testable acceptance criteria.
4. Execute a first useful work unit.
5. Validate with the strongest available deterministic checks.
6. If criteria fail, identify the cause and change the approach.
7. Respect a maximum of three attempts by default.
8. Stop on safety violations, authorization gaps, or resource exhaustion.
9. Return a concise session report with evidence and limitations.

Do not claim persistent session storage, real token accounting, or automated retries unless the host exposes those capabilities.
