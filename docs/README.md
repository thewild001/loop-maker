# ADAPTIX documentation

**Adaptive Execution Engine**  
*Discover. Decide. Execute. Adapt.*

ADAPTIX is an open-source, provider-agnostic engine for capability-driven, controlled execution. This documentation covers its current implementation, integration boundaries and development contracts.

## Start here

| I want to... | Read |
|---|---|
| Understand the product and current implementation status | [Project README](../README.md) |
| Install ADAPTIX into an existing host workflow | [Installation and usage](installation.md) |
| Understand the system boundaries and execution modes | [Architecture](architecture.md) |
| Integrate an agent or evaluator | [Adapter development](adapter-development.md) |
| Connect an existing host through MCP | [MCP integration guide](../integrations/mcp/README.md) |
| Understand capability discovery and deterministic selection | [Capability discovery and selection](capability-discovery-selection-v1.md) |
| Understand optional intelligent ranking | [Intelligent capability ranking](intelligent-capability-ranking-v1.md) |
| Review the product identity and naming transition | [Brand identity and migration](branding.md) |
| See planned work and release gates | [Roadmap](roadmap.md) |

## Architecture and operations

- [Architecture](architecture.md)
- [Integration model](integration-model.md)
- [Docker and MCP](docker-mcp.md)
- [External memory](external-memory.md)
- [Evolution Observer](evolution-observer.md)
- [End-to-end validation](e2e-validation.md)
- [Reach validation](reach-validation.md)

## Compatibility during the brand transition

ADAPTIX is the product name. Existing package names, Python imports, CLI commands, skill identifiers, MCP identifiers, environment variables and persistence paths retain their historical `loop-maker` / `loop_maker` names until a separately reviewed migration provides compatibility and deprecation guarantees.

Do not infer that a future-facing product name means a runtime identifier has already changed. The [branding and migration guide](branding.md) is the source of truth for naming policy.

## Implementation status

ADAPTIX is under active development. Read the project README and roadmap for current implementation status. Documentation distinguishes implemented behavior from planned architecture; a design document alone does not imply that a feature is available in the runtime.
