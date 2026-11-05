# Capability Selection and Host Execution Boundary — v1

**Product:** ADAPTIX — Adaptive Execution Engine  
**Status:** Proposed contract; not yet implemented as an end-to-end runtime flow  
**Scope:** Host-mediated execution of discovered capabilities  
**Audience:** Core maintainers, host integration authors, adapter authors

## 1. Purpose

ADAPTIX can discover, assess, filter and rank capabilities. Those operations do not make a capability executable. This document defines the missing handoff between an ADAPTIX selection decision and an execution performed by the host that owns the capability.

The contract preserves the central architectural invariant:

> ADAPTIX orchestrates work without taking ownership of the host's capabilities, credentials, runtime, permissions or invocation mechanisms.

The host remains the policy and execution authority for host-native capabilities. ADAPTIX returns a constrained decision and records the observed outcome; it does not turn a descriptor into an executable tool.

## 2. Non-goals

This contract does not introduce:

- A universal tool executor or a second tool registry.
- Credential discovery, storage, forwarding or installation.
- Permission escalation, approval bypass or implicit consent.
- Automatic invocation of MCP tools, native tools, APIs or skills.
- A requirement that every host expose introspection.
- A new LLM client or mandatory reasoning provider.

Delegated AgentAdapters remain a separate execution mode. They are trusted Python extensions invoked through the existing AgentAdapter contract; they must not be confused with host-mediated native capability execution.

## 3. Actors and trust boundaries

| Actor | Responsibility | Trust boundary |
|---|---|---|
| Host runtime | Supplies its known inventory and performs native invocation | Authoritative for its own capabilities and permissions |
| CapabilityProvider | Supplies descriptors and assessments from an explicitly allowed source | Descriptors and metadata are untrusted input |
| Discovery | Aggregates host-first and explicitly allowed supplemental results | Must not execute or authorize |
| Selector / ranker | Applies hard gates and optionally orders eligible candidates | Cannot add candidates or change authorization |
| Binding resolver | Maps a selected descriptor to a host-local invocation reference | Must not execute; must not disclose credentials |
| Host policy gate | Revalidates availability, authorization and approval at invocation time | Final authority; deny by default |
| Host invoker | Calls the native capability through the host's existing mechanism | Executes under host identity and permissions |
| Journal / evaluator | Records outcome and evaluates task-level acceptance | An execution result is not automatically task acceptance |

## 4. Normative lifecycle

The integration MUST follow this order:

1. **Inventory:** The host supplies the capabilities it already knows and is willing to expose to ADAPTIX. Supplemental providers are queried only when explicitly allowlisted.
2. **Discovery:** ADAPTIX normalizes descriptors and preserves provider/source provenance. Discovery is read-only.
3. **Assessment:** Availability and authorization are represented separately and scoped to the operation and execution context. Unknown values are not eligible.
4. **Selection:** Deterministic filters enforce operation compatibility, interface/category constraints, provider policy, tags, availability and authorization. Approval-required candidates remain separate.
5. **Optional ranking:** A ranker may reorder only the deterministically eligible candidate IDs. The output must be an exact permutation; otherwise the deterministic order is retained.
6. **Decision handoff:** ADAPTIX returns the selected descriptor, operation, reasons, assessment scope and opaque interface reference. It does not return a callable, credential or executable closure.
7. **Binding resolution:** The host resolves the opaque reference against its own registry/session. Resolution is local to the host and does not invoke the capability.
8. **Invocation-time policy gate:** Immediately before invocation, the host rechecks that the capability and operation still exist, are available, and are authorized. Any required approval must be obtained through the host's established approval mechanism. A stale assessment is not an execution grant.
9. **Invocation:** The host invokes the capability using its native tool, MCP client, API client, skill mechanism or other existing runtime. ADAPTIX does not proxy host-native calls.
10. **Outcome recording:** The host records a bounded result, status, timing/usage where available, and sanitized error/evidence through the existing session journal.
11. **Task evaluation:** The configured domain evaluator assesses task-level acceptance independently. A successful tool call is not equivalent to a completed objective.
12. **Adaptation:** The orchestration loop may use evaluation feedback to plan another bounded iteration, stop, or request human intervention.

A host may combine steps internally, but it MUST preserve the trust boundaries and observable semantics.

## 5. Selection handoff contract

The handoff is a decision record, not an invocation request.

Minimum logical fields:

| Field | Meaning |
|---|---|
| `decision_id` | Unique identifier for this selection decision |
| `capability_id` | Stable descriptor ID from the request inventory |
| `provider_id` / `source` | Provenance of the descriptor |
| `operation_id` | Exact operation selected |
| `interface_kind` | Host-facing interface classification |
| `interface_reference` | Opaque reference meaningful only to the owning host |
| `assessment` | Availability, authorization, assessed-at time and context |
| `rank` / `reasons` | Explainable selection order |
| `inventory_context` | Session or request context to which the decision applies |

The decision MUST NOT contain executable code, live client objects, access tokens, passwords, private keys or other credentials. The host MUST NOT treat a returned `authorization=allowed` assessment as a substitute for its own invocation-time check.

The descriptor's `metadata` is descriptive, untrusted data. It MUST NOT be interpreted as executable instructions or policy.

## 6. Failure and recovery semantics

| Condition | Required behavior |
|---|---|
| No eligible capability | Return an explicit no-match result; do not invoke |
| Approval required | Return a separate approval-required result; wait for host approval |
| Assessment missing/unknown | Reject from eligible set |
| Assessment context mismatch | Reject; obtain a fresh assessment |
| Capability disappeared | Host returns a stale-binding/unavailable outcome; rediscover |
| Permission revoked | Host denies invocation; record denial without retrying around policy |
| Binding cannot be resolved | Return a resolution failure; do not guess another reference |
| Invocation timeout/error | Host returns a normalized failure; retry only under explicit retry policy |
| Ranker unavailable/invalid | Use deterministic ordering |
| Provider failure | Preserve successful inventories and report partial discovery |

No failure path may silently broaden permissions or switch to an unreviewed provider.

## 7. Security requirements

- Revalidate availability and authorization at the point of use (TOCTOU protection).
- Bind decisions to an explicit host/session context where the host can provide one.
- Do not share assessments across contexts unless they are explicitly context-free.
- Treat provider descriptors, names, descriptions, tags, schemas and metadata as untrusted input.
- Enforce size/depth limits when accepting host-supplied JSON inventories.
- Keep secrets and raw sensitive tool outputs out of capability descriptors and journal metadata.
- Require explicit host approval for approval-gated operations.
- Do not allow a ranker to add, remove, mutate or authorize candidates.
- Log decision IDs and normalized outcomes without logging credentials or unnecessary payloads.

## 8. Relationship to existing ADAPTIX contracts

This design composes existing components rather than replacing them:

- `CapabilityProvider`, `CapabilityDiscovery` and `CapabilityInventory` provide discovery.
- `DeterministicCapabilitySelector` and `CapabilityRankingPipeline` provide constrained selection.
- `AgentAdapter.execute` remains the delegated-agent boundary.
- `LoopEngine` remains responsible for bounded delegated execution and independent evaluation.
- The MCP session journal remains the in-agent persistence path.

A future implementation may add a small decision/result service and MCP tools for host inventory submission and selection. It must not add a generic host-native tool executor to the Core.

## 9. Implementation sequence

1. Add a pure, framework-neutral decision/result contract and validation tests.
2. Add a host-facing MCP operation that accepts a bounded inventory snapshot and returns a selection decision; keep the host responsible for invocation.
3. Add journal correlation between decision ID, session iteration and sanitized invocation outcome.
4. Add invocation-time revalidation guidance and contract tests for stale/denied bindings.
5. Validate the complete flow with at least two distinct host integrations before claiming host execution support.

Each stage must preserve the existing CLI, package/import names, MCP identifiers and storage compatibility unless a separate migration is reviewed.

## 10. Acceptance criteria

- A host can submit its own inventory without installing or registering its native tools inside ADAPTIX.
- Supplemental discovery remains explicit and allowlisted.
- Unauthorized, unknown, unavailable and approval-required capabilities never enter the eligible execution set.
- The decision output contains no executable binding or credential.
- The host resolves and invokes through its existing runtime.
- Permission revocation between selection and invocation prevents execution.
- Invocation outcome and task-level evaluation remain distinct.
- Ranker failure falls back deterministically.
- The Core has no dependency on a concrete host, tool SDK or model provider.
- Documentation and tests distinguish implemented behavior from proposed behavior.

## 11. Current implementation status

The repository currently implements capability models, host-first discovery, deterministic selection and optional ranking. It does **not** yet implement this complete host-mediated handoff, binding resolution, invocation-time revalidation adapter or decision-correlated journal. This document is a design contract, not a claim that those runtime features are available.
