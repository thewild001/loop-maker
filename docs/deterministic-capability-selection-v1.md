# Deterministic Capability Selection v1

## Purpose

Select and rank capabilities from a request-scoped `CapabilityInventory` without
invoking them. This is the deterministic policy gate before any optional
intelligent ranking stage.

## Request contract

`SelectionRequest` describes one operation and may constrain:

- operation ID (required and matched exactly);
- allowed capability categories and interface kinds;
- required capability tags;
- allowed and excluded providers;
- preferred providers for stable ranking;
- whether degraded availability is acceptable;
- maximum number of eligible results.

The objective may be carried as context, but v1 does not infer semantic
relevance from free-form prose. That is deliberately left for a future optional
ranker, which must operate only on the deterministic eligible set.

## Mandatory selection gates

A candidate must pass all of these checks:

1. It declares the requested operation.
2. Its category and interface satisfy requested filters.
3. Its provider satisfies allow/deny constraints.
4. It declares every required tag.
5. It has an assessment for the requested operation or a capability-wide
   assessment. Assessments for other operations are never applicable.
6. Availability is `AVAILABLE`, or `DEGRADED` when explicitly permitted.
7. Authorization is exactly `ALLOWED`.

The selector fails closed:

- missing or unknown availability is rejected;
- unknown or denied authorization is rejected;
- `REQUIRES_APPROVAL` is reported separately and is never returned as eligible;
- missing assessments are rejected.

Assessment applicability and precedence are evaluated in this order:

1. Filter to capability-wide assessments (`operation_id=None`) and assessments
   for the exact requested operation. Assessments for unrelated operations are
   discarded; if no applicable assessment remains, selection fails closed.
2. Filter to context-free assessments and assessments whose `context_ref`
   exactly matches the request. A request without a context can use only
   context-free assessments.
3. Prefer operation-specific assessments over capability-wide assessments.
   Within the same operation scope, prefer context-specific assessments over
   context-free defaults.
4. Within an equal scope, use the newest assessment. Conflicting assessments
   with the same timestamp resolve conservatively.

This ordering means an operation-specific global denial cannot be overridden
by a context-specific capability-wide allow, while a context-specific assessment
for the requested operation overrides its global counterpart. This is not a
substitute for freshness policy: the host must revalidate availability and
authorization at the invocation boundary to avoid time-of-check/time-of-use errors.

`SelectionRequest` also enforces strict runtime types: boolean opt-in for
degraded availability, positive integer result limits (excluding booleans), enum
tuples for categories/interfaces, and tuple-of-non-empty-string collections
for tags and provider constraints.

## Deterministic ranking

Eligible candidates are ordered by:

1. explicit provider preference order;
2. case-insensitive capability name;
3. stable capability ID.

Ranks are one-based and repeatable for the same inventory and request.
`max_results` limits the eligible list after ranking. Approval-required
candidates and rejected candidates remain separately explainable.

## Output

`SelectionResult` contains:

- `selected`: eligible candidates with rank, assessment and reasons;
- `approval_required`: candidates blocked pending host approval;
- `rejected`: candidates with a stable rejection code and explanation.

## Non-goals and safety boundary

- No execution, invocation, binding resolution or permission grant.
- No LLM dependency or provider-specific behavior.
- No semantic claim that a tool is relevant merely because its description
  resembles the objective.
- No generic JSON Schema compatibility inference in v1.
- No automatic provider discovery or installation.

The host remains the source of truth for permissions and performs the final
invocation-time checks. A future LLM ranker may reorder only the eligible
candidate set; it cannot override these hard filters.
