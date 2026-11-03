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
| `loop_observation_groups` | Find recurring candidate groups |

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

## Limitations in Phase 1

- Capture is explicit/manual through the host agent; no host hooks are installed.
- Grouping is deterministic and heuristic; it does not claim semantic similarity.
- No skill is modified, staged, validated or published.
- No direct Engram connection is created. If the host exposes Engram MCP tools, the agent may use them independently.
- No scheduled review or autonomous capture is included.
