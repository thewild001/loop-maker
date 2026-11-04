# Capability Discovery & Selection — Technical Design v1.0

**Project:** Loop Maker  
**Status:** Proposed — pending architectural review  
**Scope:** Capability discovery, normalization, inventory and selection  
**Target:** Adaptive Execution System foundation

## 1. Purpose

Capability Discovery & Selection gives Loop Maker a host-agnostic way to learn which capabilities are available, represent them consistently, and select suitable candidates for a task.

It does not take ownership of host capabilities, credentials, permissions, installation, or execution. The host remains authoritative for its own environment and remains responsible for invoking native capabilities.

### Goals

- Consume an explicit capability inventory supplied by the host.
- Optionally augment that inventory through explicitly configured and authorized providers.
- Normalize descriptors without erasing their provenance.
- Represent operations, interfaces, constraints, availability and authorization separately.
- Filter candidates deterministically before optional intelligent ranking.
- Preserve compatibility with existing AgentAdapter and entry-point APIs.

### Non-goals

- Universal introspection of arbitrary agent hosts.
- Automatic installation, login, credential discovery or configuration.
- A new agent runtime or tool execution framework.
- A persistent global capability database in the MVP.
- Permission escalation or bypassing host policy.

## 2. Architectural invariants

| ID | Invariant |
|---|---|
| CAP-001 | The Core has no dependency on concrete hosts, providers, models or tool frameworks. |
| CAP-002 | Host-supplied inventory is the primary source for host-native capabilities. |
| CAP-003 | Supplemental discovery is explicit, optional and policy-controlled. |
| CAP-004 | Discovery does not imply authorization or invocability. |
| CAP-005 | Selection cannot expand permissions or override host policy. |
| CAP-006 | Every discovered source retains provenance. |
| CAP-007 | Equivalent-looking capabilities are not automatically merged. |
| CAP-008 | External descriptors and metadata are untrusted input. |
| CAP-009 | Partial provider failure does not invalidate successful sources. |
| CAP-010 | Availability and authorization are revalidated at the invocation boundary. |
| CAP-011 | No automatic installation or credential management. |
| CAP-012 | A host that exposes no inventory is not assumed to support introspection. |

## 3. Terminology and model boundaries

These concepts must not be conflated:

- **Capability:** logical function that may help accomplish a task.
- **Operation:** specific action supported by a capability.
- **Provider:** component that discovers descriptors from a source.
- **Source:** concrete origin/instance from which a descriptor was obtained.
- **Interface:** mechanism and reference through which the host can consume the capability.
- **Assessment:** contextual, time-bound knowledge about availability and authorization.
- **Inventory:** normalized snapshot of descriptors and their source assessments.
- **Selector:** chooses among eligible candidates.
- **Binding resolver:** resolves a selected descriptor to an opaque host-owned invocation binding. It does not execute it.

### Category versus interface

Capability category describes logical behavior: `AGENT`, `TOOL`, `SKILL`, `EVALUATOR` (extensible).

Interface kind describes access mechanism: `NATIVE`, `MCP_TOOL`, `MCP_RESOURCE`, `MCP_PROMPT`, `PYTHON_ENTRY_POINT`, `SKILL_ACTIVATION`, `API`, `DELEGATED_AGENT`.

MCP is an interface/transport family, not a capability category. A plugin is a packaging or extension mechanism, not necessarily a capability. A plugin may provide an agent, tool or evaluator. A skill may be instructions consumed by a host agent and is not necessarily directly invocable.

## 4. Conceptual architecture

```text
HOST ENVIRONMENT
  ├── Native tools / agents / skills / MCP clients / plugins
  └── Explicit Host Capability Inventory
                    |
          Hybrid Discovery Coordinator
          ├── Host Inventory Provider (primary)
          └── Supplemental Providers (opt-in)
                    |
              Normalization
                    |
          Request-scoped Capability Inventory
          ├── descriptors + operations
          ├── source provenance
          └── contextual assessments
                    |
          Deterministic Eligibility Filter
          ├── functional compatibility
          ├── availability
          ├── authorization / approval
          └── task and policy constraints
                    |
          Optional Intelligent Ranking
                    |
              Selection Validator
                    |
             Selection Result
                    |
       Existing Loop Maker Core / Host
                    |
       Host or trusted adapter executes
```

Discovery and selection produce information for planning/orchestration. They do not execute selected capabilities.

## 5. Capability descriptor contract

The descriptor is reusable metadata. It must not embed mutable, context-free claims that a capability is currently available or authorized.

Illustrative Python contract (exact field types and validation limits are to be finalized during implementation):

```python
@dataclass(frozen=True)
class CapabilityDescriptor:
    id: str
    name: str
    description: str
    category: CapabilityCategory
    source: CapabilitySource
    interface: CapabilityInterface
    operations: tuple[CapabilityOperation, ...]
    constraints: CapabilityConstraints
    metadata: Mapping[str, object]
```

### Category

```python
class CapabilityCategory(StrEnum):
    AGENT = "agent"
    TOOL = "tool"
    SKILL = "skill"
    EVALUATOR = "evaluator"
```

The enum is extensible. Do not add `MCP` or `PLUGIN` as categories merely because they are transports or packaging formats.

### Source and identity

```python
@dataclass(frozen=True)
class CapabilitySource:
    provider_id: str
    source_type: str
    native_id: str
    provenance: str | None = None
```

A descriptor has a stable Loop Maker ID and retains the provider's native identifier. The same logical function discovered from two sources remains represented by two source-specific descriptors unless an explicit equivalence relation is established. Never merge based on display name alone.

### Interface and operation

```python
@dataclass(frozen=True)
class CapabilityInterface:
    kind: InterfaceKind
    reference: str
    input_schema: Mapping[str, object] | None = None
    output_schema: Mapping[str, object] | None = None

@dataclass(frozen=True)
class CapabilityOperation:
    id: str
    description: str
    input_schema: Mapping[str, object] | None = None
    output_schema: Mapping[str, object] | None = None
```

Schemas are descriptive contracts, not proof that an operation is safe or authorized. Unknown or invalid schemas must not be guessed by an LLM.

A capability may expose multiple operations. A skill descriptor may instead describe activation/instruction semantics delegated to the host.

## 6. Contextual assessments

Availability and authorization can vary by operation, host, user/session, policy and time. They therefore belong in an assessment associated with a descriptor and context, not as timeless facts on the descriptor.

Illustrative model:

```python
class Availability(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

class Authorization(StrEnum):
    ALLOWED = "allowed"
    DENIED = "denied"
    REQUIRES_APPROVAL = "requires_approval"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class CapabilityAssessment:
    capability_id: str
    operation_id: str | None
    availability: Availability
    authorization: Authorization
    assessed_at: datetime
    context_ref: str | None = None
    evidence: str | None = None
```

Rules:

- `UNKNOWN` is not equivalent to `AVAILABLE` or `ALLOWED`.
- `DENIED` is ineligible.
- `REQUIRES_APPROVAL` may be returned as conditional, but cannot be invoked until the host approval flow succeeds.
- Assessments are snapshots and may become stale.
- The host remains the final authority at invocation time.

## 7. Hybrid discovery

### 7.1 Host-driven discovery

The host explicitly supplies an inventory through a documented integration contract. This is the primary path.

Loop Maker cannot assume that an MCP server can introspect the MCP client or enumerate other tools and servers connected to that client. Host injection or an explicitly configured provider is required.

### 7.2 Loop-driven supplemental discovery

Loop Maker may query additional providers only when:

1. the provider is explicitly configured/allowed;
2. the discovery policy permits the query;
3. the host inventory does not satisfy the discovery requirements or the caller requests augmentation.

No indiscriminate scanning, automatic installation or implicit login.

### 7.3 Provider contract

```python
class CapabilityProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    async def discover(
        self, context: DiscoveryContext
    ) -> ProviderDiscoveryResult: ...
```

Each provider result carries its own status, completeness, descriptors and errors. A failed provider must not erase successful results from other providers.

```python
@dataclass
class ProviderDiscoveryResult:
    provider_id: str
    capabilities: list[CapabilityDescriptor]
    status: ProviderStatus
    complete: bool
    errors: list[DiscoveryError]
    source_version: str | None = None
```

Completeness is scoped to that provider's declared discovery scope; it does not claim that the whole host has been discovered.

### 7.4 Initial providers

MVP:
- `HostInventoryProvider`: accepts an explicit host-provided inventory.
- `EntryPointAdapterProvider`: projects existing trusted `loop_maker.agents` adapters into descriptors.

Later, only where integration contracts exist:
- MCP inventory provider;
- skill inventory provider;
- other host/plugin/agent providers.

Existing Python entry-point loading executes installed Python code via `point.load()`. It is trusted extension loading, not safe passive inspection or sandboxing. Only explicitly trusted packages may be installed.

## 8. Inventory and registry

The MVP uses a request- or session-scoped in-memory inventory snapshot.

Responsibilities:
- validate and normalize descriptors;
- preserve provider and native provenance;
- associate contextual assessments;
- detect conflicting IDs without silently overwriting;
- retain explicit equivalence relationships without merging descriptors;
- expose query operations to the selector.

No new persistent database is justified for the MVP. TTL caching may be considered later, with explicit invalidation and re-assessment rules.

## 9. Hybrid selection

### 9.1 Deterministic eligibility filter (mandatory)

Before any intelligent ranking, candidates must pass deterministic checks for:
- required operation coverage;
- schema/contract compatibility where schemas are available;
- availability required by the task;
- authorization and approval state;
- task constraints and host policy;
- provider/source allowlists.

Missing information is not inferred as a security permission. Candidates with unknown authorization are not executable. They may be reported as unresolved/conditional if the workflow supports host-side approval.

### 9.2 Optional intelligent ranking

An optional selector may rank only the eligible candidates using task suitability, coverage, quality evidence, latency, cost and other non-security preferences.

The selector:
- is not a required Core dependency;
- may be supplied by the host or an adapter;
- receives no credentials, secrets or unnecessary private context;
- treats descriptor text as untrusted data;
- cannot create capabilities, alter permissions, invent schemas or bypass deterministic filters.

### 9.3 Fallback and validation

If intelligent ranking is unavailable or fails, use a deterministic fallback with documented priorities.

A post-selection validator rechecks that every selected candidate belongs to the eligible set and still satisfies constraints. Immediately before invocation, the host/adapter must revalidate current availability and authorization to mitigate TOCTOU changes.

### 9.4 Contracts

```python
class CapabilitySelector(Protocol):
    async def select(
        self,
        objective: Task,
        inventory: CapabilityInventory,
        constraints: SelectionConstraints,
    ) -> SelectionResult: ...

@dataclass
class SelectionResult:
    selected: list[SelectedCapability]
    rejected: list[RejectedCapability]
    rationale: str
    unresolved_requirements: list[str]
```

The exact selection strategy may return multiple capabilities when the task requires composition. The contract must preserve per-candidate rationale and rejection reasons.

## 10. Binding resolution and execution boundary

Use the name `CapabilityBindingResolver` to avoid implying that a resolver executes operations.

It maps a selected descriptor to a host-owned opaque binding or integration reference. It does not call the tool, start an agent, perform network requests, or bypass host policy.

Execution remains with:
- the connected host for native tools, MCP tools and skills;
- a trusted adapter for delegated execution already supported by Loop Maker.

The host's normal approval, audit and permission mechanisms remain authoritative.

## 11. Compatibility with current Loop Maker

Current relevant components:
- `contracts.py`: `Task`, `AgentResult`, `EvaluationResult`, `LoopConfig`, `LoopResult`, `AgentAdapter`, `Evaluator`.
- `registry.py`: Python entry-point discovery for agents and evaluators.
- `mcp_server.py`: `loop_list_agents`, `loop_run`, session tools and `loop-maker://agents`.
- `pyproject.toml`: `loop_maker.agents` and `loop_maker.evaluators` entry-point groups.

Compatibility rules:
1. Preserve `AgentAdapter.capabilities() -> dict` during the transition.
2. Add a normalization adapter; do not force existing third-party adapters to migrate immediately.
3. Keep `loop_list_agents` and `loop-maker://agents` backward compatible.
4. Add capability-oriented MCP APIs only after the host inventory input contract is defined and tested.
5. Do not claim host tool/skill/MCP discovery merely because Python adapters can be loaded.

## 12. Proposed package layout

```text
src/loop_maker/
  capabilities/
    __init__.py
    models.py
    providers.py
    discovery.py
    inventory.py
    selector.py
    binding.py
    normalization.py
  contracts.py
  registry.py
  mcp_server.py
```

This is a proposed layout, not a requirement to create every module at once. Keep the public contracts small and avoid premature abstraction.

## 13. Security and trust

- Treat provider output, descriptions, schemas and metadata as untrusted input.
- Validate size, shape, identifiers and schema structure before registration.
- Do not execute code during generic discovery.
- Keep trusted Python entry-point loading clearly separate from passive inventory discovery.
- Do not expose secrets to intelligent ranking.
- Do not let LLM output authorize, install or invoke capabilities.
- Enforce provider allowlists and host policy.
- Revalidate permission and availability at invocation time.
- Preserve provenance and actionable error reporting.
- Do not interpret a skill's text as executable authority.

## 14. Contract test matrix

| ID | Scenario | Expected behavior |
|---|---|---|
| CDS-001 | Explicit host inventory | Normalize and register descriptors. |
| CDS-002 | Partial host inventory | Preserve scope/completeness metadata. |
| CDS-003 | Supplemental provider failure | Keep successful provider results and report the error. |
| CDS-004 | Duplicate native IDs from distinct sources | Preserve provenance; do not silently overwrite. |
| CDS-005 | Similar names, different semantics | Do not merge automatically. |
| CDS-006 | Unknown authorization | Never mark executable. |
| CDS-007 | Denied operation | Exclude from eligible candidates. |
| CDS-008 | Approval required | Return conditional state; require host approval. |
| CDS-009 | Unavailable operation | Exclude when availability is mandatory. |
| CDS-010 | Intelligent selector unavailable | Deterministic fallback works. |
| CDS-011 | LLM proposes ineligible capability | Post-validator rejects it. |
| CDS-012 | Malformed descriptor/schema | Reject affected descriptor with source error. |
| CDS-013 | Empty inventory | Return valid empty result and unresolved requirements. |
| CDS-014 | Permission changes after discovery | Invocation boundary rejects stale authorization. |
| CDS-015 | Unapproved provider | Provider is not queried. |
| CDS-016 | Skill descriptor | Do not assume direct tool invocability. |
| CDS-017 | Existing adapter capabilities dict | Normalize without breaking legacy adapter. |
| CDS-018 | Legacy MCP agent listing | Existing response remains compatible. |

## 15. Acceptance criteria

The MVP is complete when:
- typed descriptor, operation, source, interface and assessment contracts exist;
- host inventory is accepted explicitly;
- existing trusted agent entry points can be projected without API breakage;
- provider failures are isolated and reported;
- an in-memory inventory preserves provenance;
- deterministic eligibility filtering is mandatory;
- intelligent ranking is optional and constrained to eligible candidates;
- deterministic fallback and post-validation are tested;
- stale authorization is rejected at invocation boundary;
- existing agent APIs remain backward compatible;
- at least one real host integration is tested end-to-end before claiming host compatibility.

## 16. Incremental implementation plan

1. Finalize contracts and validation rules.
2. Add normalization for legacy `AgentAdapter.capabilities()`.
3. Add explicit `HostInventoryProvider` and request-scoped inventory.
4. Adapt trusted entry-point discovery without changing its trust model.
5. Implement deterministic filtering and selection result reporting.
6. Add optional intelligent ranking behind a protocol and deterministic fallback.
7. Add binding resolution contract and invocation-time revalidation hooks.
8. Define and test host-facing/MCP inventory exchange only with a real host integration.
9. Run contract, regression, security-boundary and host E2E tests.

Each implementation phase should be delivered through a reviewable PR. No direct changes to `main`, and no merge without explicit approval.

## 17. Open decisions before implementation

These points require explicit resolution during contract review:
- Whether capability IDs are provider-scoped or globally namespaced (recommendation: globally unique normalized ID plus source-specific native ID).
- Exact schema validation level and supported JSON Schema draft.
- Whether approval-required candidates appear in the primary selection or a separate conditional list (recommendation: separate conditional list).
- Whether selection supports ordered fallback chains in v1 or only ranked candidates (recommendation: ranked candidates first; fallback chain later).
- Whether assessment evidence stores raw details or only safe references (recommendation: references/summaries; never secrets).
- Whether a host inventory is supplied as Python objects, JSON payload or both (recommendation: canonical validated JSON-compatible payload at the boundary, normalized internally).

These are implementation gates, not reasons to add provider-specific dependencies to the Core.

## 18. Architectural decision

**Loop Maker discovers, normalizes, evaluates and selects existing capabilities. It does not appropriate them, replace their execution mechanisms or expand their permissions.**

The host remains authoritative. Providers complement discovery. The inventory preserves source context. Deterministic policy filters define eligibility. Optional intelligence ranks eligible alternatives. The host or trusted adapter executes.

This separation is the foundation for evolving Loop Maker from an execution orchestrator into an Adaptive Execution System.
