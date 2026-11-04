# Intelligent Capability Ranking v1

## Purpose

Add optional semantic relevance ordering without weakening deterministic
eligibility or making an LLM a core dependency.

## Pipeline

1. `DeterministicCapabilitySelector` applies operation, category, interface,
   provider, tag, availability, authorization and assessment-scope gates.
2. The optional `CapabilityRanker` receives only the resulting eligible set.
3. The pipeline validates that the returned IDs are an exact permutation of
   eligible IDs: no additions, omissions or duplicates.
4. `max_results` is applied after ranking.
5. If no ranker is configured, it raises, or its output is malformed, the
   deterministic order is returned unchanged.

Approval-required and rejected capabilities are never passed to the ranker.

## Contract

The provider-neutral `CapabilityRanker.rank(context, candidates)` contract
returns candidate IDs in preferred order. The context contains only the
operation ID and optional objective. Candidate views contain identity,
descriptive fields, category, provider, interface, operation description and
tags. Assessment evidence, context references and arbitrary metadata are
excluded.

The core does not define an LLM client, prompt format, model, timeout policy or
provider. A host integration may implement the protocol with any suitable
reasoning system or a non-LLM ranker.

## Security boundary

- The ranker cannot authorize, execute, invoke or resolve a capability binding.
- The ranker cannot change availability, authorization or eligibility.
- Invocation-time permission and availability checks remain mandatory at the
  host boundary (including TOCTOU revalidation).
- Capability names, descriptions, operation descriptions and tags originate
  outside the ranker and must be treated as untrusted data. LLM adapters must
  delimit them as data, ignore embedded instructions, minimize prompt context
  and never grant tool access to the ranking call.
- Ranker output is untrusted and validated as an exact permutation.
- Any exception or invalid output degrades to deterministic ordering.

## Non-goals

No automatic LLM selection, model management, provider integration, execution,
binding resolution, permission changes, candidate synthesis, or generic
capability compatibility inference.
