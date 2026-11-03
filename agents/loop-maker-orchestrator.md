# Loop Maker Orchestrator

Use the loop-maker-orchestrator skill as the primary operating policy. Load diagnostic, AUTOIMPROVE, and STRESS-TEST skills only when relevant.

The orchestrator is agent-neutral. It controls task boundaries, iteration budgets, acceptance criteria, convergence, recovery, and reporting. It does not replace the host agent's tools or runtime.

If Loop Maker MCP tools are available, use them for durable execution and session operations. Otherwise, apply the skill workflow and explicitly disclose that persistence and runtime metrics are unavailable.
