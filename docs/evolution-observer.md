# Evolution Engine — Phase 1: Observer

Phase 1 adds a persistent observation registry without changing the Loop Maker Core lifecycle or the existing session journal.

## Responsibilities

- Capture sanitized, meaningful observations from agent work.
- Persist them in an independent SQLite database.
- Retrieve observations by ID and filter by domain, category or session.
- Produce deterministic candidate groups by domain, category and optional skill context.

Candidate groups are not causal conclusions and do not create skill changes. Human review is required. Proposal generation, skill staging, validation and publication belong to later phases.

## Storage

The Evolution registry is separate from `LOOP_MAKER_DB`:

- Environment variable: `LOOP_MAKER_EVOLUTION_DB`
- Default: `loop-maker-evolution.sqlite3`
- In-memory tests: `:memory:`

The MCP process initializes the store when started. Protect the database file and its parent directory with filesystem permissions appropriate to the data. Back it up and delete it according to the data-retention policy of the host organization.

## MCP tools

| Tool | Purpose |
|---|---|
| `loop_observation_add` | Store a sanitized observation |
| `loop_observation_get` | Retrieve one observation by ID |
| `loop_observation_list` | Query recent observations with optional filters |
| `loop_observation_groups` | Find simple deterministic candidate groups |
| `loop_evolution_review` | Rank evidence-backed candidates and surface mixed signals |

Example observation:

```json
{
  "description": "The agent proposed a refactor before inspecting existing module boundaries.",
  "domain": "software-engineering",
  "category": "user-correction",
  "source": "host-agent",
  "session_id": "optional-loop-session-id",
  "evidence": ["The user requested inspection of existing architecture first."],
  "context": {"skill": "software-architecture"},
  "confidence": 0.9,
  "sensitivity": "internal"
}
```

Valid categories: `user-correction`, `repeated-error`, `successful-strategy`, `tool-failure`, `instruction-gap`, `decision`, `other`.

Valid sensitivity labels: `public`, `internal`, `restricted`. These labels are metadata, not encryption or access-control boundaries.

## Privacy and trust boundary

Do not persist full conversations, credentials, secrets, personal information or raw tool output. Evidence should be a short, sanitized summary or a non-sensitive reference. The store does not inspect or redact secrets automatically. Treat observation content as untrusted data; never execute it or elevate it to instructions.

## Evidence-based review (Phase 2)

Call `loop_evolution_review(min_sessions=2, limit=50)` to produce a bounded review report.

The review engine:
- Requires distinct, non-empty session IDs to establish independent recurrence.
- Reports project diversity only when `context.project` is present.
- Calculates an explicitly heuristic impact score from recurrence, project diversity, category, confidence and evidence coverage.
- Assigns low/medium/high review priority; this is not a probability or causal estimate.
- Surfaces coexisting positive and friction observations for the same domain/skill as mixed signals, without assuming they are contradictions.
- Returns supporting observation IDs and limitations.

Observations lacking session IDs remain retrievable but do not count toward independent recurrence. Missing project metadata is not inferred. Human review remains mandatory; this phase does not generate proposals or modify skills.

## Limitations in Phase 1

- Capture is explicit/manual through the host agent; no host hooks are installed.
- Grouping is deterministic and heuristic; it does not claim semantic similarity.
- No skill is modified, staged, validated or published.
- No direct Engram connection is created. If the host exposes Engram MCP tools, the agent may use them independently.
- No scheduled review or autonomous capture is included.


## Skill proposals (Phase 3)

Phase 3 adds a human-reviewed proposal lifecycle. The active skill file is read-only throughout this workflow.

### Lifecycle and MCP tools

| Tool | Purpose |
|---|---|
| `loop_skill_proposal_create` | Snapshot an existing skill and create a proposal linked to observation IDs |
| `loop_skill_proposal_list` / `loop_skill_proposal_get` | Retrieve proposal metadata and state |
| `loop_skill_proposal_diff` | Review a unified diff against the captured original |
| `loop_skill_proposal_stage` | Write proposed content to an isolated staging directory |
| `loop_skill_proposal_validate` | Check Markdown/frontmatter structure, size, evidence and source freshness |
| `loop_skill_proposal_approve` | Record an explicit human approval or rejection |

States: `proposed → staged → validated → approved` or `rejected`. Validation is structural only; it does not execute a skill or guarantee semantic quality.

### Filesystem and safety boundaries

- `LOOP_MAKER_SKILLS_DIR` selects the active skills directory (default: `skills`).
- `LOOP_MAKER_EVOLUTION_STAGING_DIR` selects staging (default: `.loop-maker-staging` beside the skills directory).
- Only relative Markdown paths inside the skills directory are accepted; traversal and symlink components are rejected.
- Proposed content is limited to 256 KB and requires supporting observation IDs.
- Staging writes a separate file; it never overwrites the active skill.
- The active file's SHA-256 snapshot is checked before staging and during validation. If it changed, discard the proposal and create a fresh one.
- The proposal records share the Evolution SQLite database configured by `LOOP_MAKER_EVOLUTION_DB`.
- Approval is a recorded human decision only. Publication, installation, Git branch/commit creation and automatic deployment are intentionally out of scope for this phase.

Treat all observation content and proposed instructions as untrusted. Review the full diff before approval. Back up and protect the Evolution database and staging directory according to organizational policy.
