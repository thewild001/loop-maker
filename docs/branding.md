# ADAPTIX — Brand identity and migration guide

**Product name:** ADAPTIX  
**Product category:** Adaptive Execution Engine  
**Tagline:** Discover. Decide. Execute. Adapt.  
**Personality:** Open source, engineering-first, provider-agnostic.

This document is the source of truth for product naming and visual identity during the gradual transition from Loop Maker to ADAPTIX.

## 1. Positioning

ADAPTIX is an open-source, provider-agnostic adaptive execution engine. It discovers available capabilities, determines which are eligible for a goal, coordinates controlled execution and evaluates outcomes so an execution strategy can adapt.

**Short description**

> An open-source adaptive execution engine for discovering, selecting, coordinating and evaluating capabilities.

**Expanded description**

> ADAPTIX provides the adaptive execution layer between an objective and the capabilities available in an AI environment. It works with the host's models, tools, agents, memory, runtime and permissions instead of replacing them.

## 2. Product principles

- **Host-respectful:** the host remains the authority for its own capabilities, permissions and execution environment.
- **Provider-agnostic:** no model vendor, agent framework or tool protocol is mandatory.
- **Capability-driven:** discovery and selection are explicit, contextual operations.
- **Controlled adaptation:** intelligent ranking may improve ordering, but deterministic eligibility and authorization constraints remain mandatory.
- **Composable:** integrations are added through stable contracts and adapters.
- **Evidence-oriented:** evaluation must be grounded in observable results.
- **Open source:** interfaces, limitations and implementation status should be transparent.

## 3. Logo concept — Adaptive Core

The selected logo direction is **Adaptive Core**.

The mark represents a stable central execution core connected to a changing environment. Its visual language combines:
- a central core: decision and coordination;
- four outward connections: capabilities and integrations;
- a geometric frame: control, boundaries and predictable execution;
- open gaps: extensibility rather than a closed platform.

The mark is intentionally abstract. It should not imply that ADAPTIX is itself an LLM, a neural network or an autonomous agent.

Primary asset: [`assets/adaptix-core.svg`](../assets/adaptix-core.svg).

### Clear-space and usage

- Preserve clear space around the mark equal to at least one quarter of its width.
- Use the SVG on dark or light surfaces; do not recolor individual paths arbitrarily.
- Do not stretch, rotate, add gradients, shadows or decorative effects.
- Use the standalone mark for repository avatars, CLI headers and compact navigation.
- Pair the mark with the ADAPTIX wordmark and tagline in larger brand placements.
- The source SVG is the canonical vector asset. Raster exports should be generated from it, not redrawn independently.

## 4. Visual system

| Token | Value | Intended use |
|---|---|---|
| Midnight | `#111827` | Primary dark surface |
| Electric Blue | `#2563EB` | Primary interaction and links |
| Adaptive Cyan | `#22D3EE` | Core identity and highlights |
| Signal Lime | `#A3E635` | Success and convergence states only |
| Cloud | `#F3F4F6` | Light surfaces and contrast |

Use Midnight and Cloud as neutral foundations. Electric Blue and Adaptive Cyan carry the identity. Signal Lime is a semantic accent, not a general brand fill.

Typography direction:
- Wordmark: geometric sans-serif, bold, uppercase.
- Headings: modern sans-serif with clear hierarchy.
- Body and code: highly legible system sans-serif and monospace.
- Prefer restrained typography over futuristic display fonts.

## 5. Voice and messaging

**Voice:** precise, technically credible, direct, transparent and constructive.

Prefer:
- adaptive execution;
- capability discovery and selection;
- provider-agnostic;
- controlled execution;
- host-native capabilities;
- deterministic constraints;
- evidence-based evaluation.

Avoid unsupported claims such as:
- fully autonomous;
- self-thinking;
- works with every agent;
- zero-configuration;
- universal compatibility;
- production-ready, unless validated for the specific integration.

## 6. Naming conventions

| Surface | Current transition name | Policy |
|---|---|---|
| Product / public brand | ADAPTIX | Adopt now |
| Product category | Adaptive Execution Engine | Adopt now |
| Repository slug | `loop-maker` | Keep during transition |
| Python distribution | `loop-maker-orchestrator` | Keep; changing requires release and dependency plan |
| Python import | `loop_maker` | Keep; compatibility alias/migration needed before replacement |
| CLI | `loop-maker`, `loop-maker-mcp` | Keep; do not break scripts |
| Skill commands | `/loop-maker-*` | Keep; installed host paths are user-facing contracts |
| MCP tools/resources | `loop_*`, `loop-maker://*` | Keep; protocol identifiers are integration contracts |
| SQLite/env vars | `loop-maker.sqlite3`, `LOOP_MAKER_*` | Keep; persistence and deployment compatibility |
| GitHub URLs | `thewild001/loop-maker` | Keep until repository rename is separately planned |

Do not introduce new public identifiers containing `adaptix` for runtime interfaces until a dedicated compatibility proposal is reviewed.

## 7. Gradual migration policy

### Phase 1 — Brand adoption (this change)
- Present ADAPTIX as the product name in README and project metadata description.
- Add the canonical Adaptive Core SVG.
- Publish this branding and migration guide.
- Preserve repository, package, import, CLI, skill, MCP and persistence identifiers.

### Phase 2 — Developer experience alignment
- Consider new CLI aliases while retaining old commands.
- Add compatibility tests and deprecation policy before changing any identifier.
- Update examples, install scripts and host-specific integration documentation together.

### Phase 3 — Distribution and repository migration
- Evaluate a repository rename and package distribution rename independently.
- Verify namespace availability and ownership before claiming names.
- Provide migration instructions, release notes and a compatibility window.
- Never silently rename database files, environment variables, entry points or MCP identifiers.

Each phase requires its own pull request and validation. Brand adoption alone is not authorization to rename runtime contracts.

## 8. Brand acceptance checklist

- [ ] ADAPTIX is the product name in public-facing copy.
- [ ] The tagline is exactly “Discover. Decide. Execute. Adapt.”
- [ ] The Adaptive Core SVG is used as the canonical mark.
- [ ] Claims match implemented and validated capabilities.
- [ ] Existing technical identifiers remain functional during transition.
- [ ] Any future identifier migration includes compatibility tests and release notes.
- [ ] Trademark, domain, package and repository availability are checked before commercial adoption.

## 9. Legal and availability note

ADAPTIX is the selected working brand, not a statement of trademark clearance. Before public commercial launch, independently verify relevant trademark registers, domains, GitHub organization/repository names, PyPI distribution names and other relevant software namespaces.
