# End-to-end validation plan

This plan separates automated checks from host-level acceptance. Passing Python CI does not prove that a skill is discoverable or behaves correctly inside a third-party agent.

## 1. Automated checks

Run from a clean checkout:

```bash
python -m pip install -e ".[dev,mcp]"
ruff check src tests
pytest -q
bash scripts/install-skills.sh --target /tmp/loop-maker-e2e
```

Verify that the installer creates the canonical skills in:
- `.agents/skills/`
- `.claude/skills/`
- `.opencode/skills/`

It should also create the Cursor and Copilot instruction files. Re-run against the same target to verify that existing files are preserved; re-run with `--force` to verify explicit replacement.

For the MCP path, configure the host with the local `loop-maker-mcp` executable and verify:
1. `loop_list_agents` returns the demo adapter and any installed trusted adapters.
2. `loop_session_start` creates a RUNNING session.
3. `loop_record_iteration` persists output and metadata.
4. `loop_get_session` returns the same session and iteration.
5. `loop_session_finish` closes the session.
6. `loop_run` with the demo adapter is treated only as a protocol smoke test, not proof of real delegated execution.

## 2. Host-level acceptance matrix

Run the same four task classes in each target host where the skill format is supported:

| Scenario | Example objective | Required evidence |
|---|---|---|
| Research | Compare three current approaches to a named technical problem | Sources are linked, claims traceable, uncertainty stated |
| Analysis | Evaluate two architecture options against explicit constraints | Assumptions, comparison criteria and trade-offs visible |
| Writing | Draft a concise technical proposal from supplied notes | Audience, requested structure and constraints respected |
| Software | Change a small isolated module in a disposable repository | Diff shown, relevant tests executed, regressions reported |

Hosts to validate independently:
- Codex
- Claude Code
- OpenCode
- Cursor

For each host record: version, operating system, skill discovery path, MCP enabled/disabled, exact invocation, task result, tool calls actually performed, and any failure. Do not mark a host supported based only on copied files or a successful MCP connection.

## 3. Pass/fail rules

A host/scenario passes only if:
- The host discovers the skill without manual prompt injection.
- The skill follows the bounded loop and adapts criteria to the task domain.
- It uses only the host's actually available tools and permissions.
- It does not invent execution, sources, test results, metrics or persistence.
- It stops at budget, authorization or safety boundaries.
- If MCP is enabled, the recorded session can be retrieved and matches the work performed.

A host is **not validated** when no real task was executed. Report partial results explicitly.

## 4. Current validation boundary

The automated CI covers Python linting, unit tests and installer smoke tests. The Bash installer can be exercised on Linux CI. The PowerShell bootstrap and all third-party host integrations still require execution in their target environments. No real provider-backed agent run is implied by the demo adapter.
