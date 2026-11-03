# Loop Maker repository instructions

This repository builds an agent-agnostic orchestration engine.

- Keep the core independent from individual agent frameworks and model providers.
- Put host-specific behavior in adapters, plugins, skills, or integration recipes.
- Do not claim an integration works until its host configuration and end-to-end test are verified.
- Do not mark a loop converged without mandatory acceptance criteria and evidence.
- Keep the demo adapter clearly identified as a fixture, never as a production agent.
- Run the test suite and lint before proposing a completed change.
- Preserve existing project configuration when writing installers.
- Treat adapter packages and agent output as untrusted across the integration boundary.
