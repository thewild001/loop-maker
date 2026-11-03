# Desarrollo de adaptadores

Un adaptador es una capa anticorrupción delgada alrededor de un agente existente. No traslades al Core la planificación del agente, la selección de modelos, su memoria ni sus políticas de herramientas.

Implementa:

- agent_id: identificador estable.
- capabilities(): metadatos veraces de capacidades.
- execute(task, context): una unidad de ejecución acotada que devuelve AgentResult.

Ejemplo:

```python
from loop_maker.contracts import AgentResult, Task

class MyAdapter:
    @property
    def agent_id(self) -> str:
        return "my-agent"

    def capabilities(self) -> dict:
        return {"execute": True, "streaming": False}

    async def execute(self, task: Task, context: dict) -> AgentResult:
        output = await my_agent_sdk.run(task.objective, context=context)
        return AgentResult(output=output, success=True, complete=True)
```

Registra el adaptador en entry points del paquete:

```toml
[project.entry-points."loop_maker.agents"]
my-agent = "my_adapter:MyAdapter"
```

El entry point ejecuta código Python. Instala únicamente paquetes de confianza. Ejecuta las pruebas de contrato y valida timeout, cancelación, artefactos y permisos antes de producción.

## Evaluator plugins

If an adapter is used with mandatory acceptance criteria, install one independent evaluator plugin. Register exactly one default evaluator in the loop_maker.evaluators entry-point group:

```toml
[project.entry-points."loop_maker.evaluators"]
default = "my_evaluator:MyEvaluator"
```

The evaluator implements async evaluate(task, result) and returns EvaluationResult with verified_criteria, failed_criteria, and an evidence dictionary keyed by each verified criterion. The Core refuses convergence when mandatory criteria are present but no evaluator is installed, when the evaluator fails, or when evidence is empty. An evaluator must verify artifacts or deterministic checks independently; it must not merely repeat the agent's claim.
