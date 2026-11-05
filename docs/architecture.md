# Arquitectura multipropósito

## Principio

ADAPTIX gestiona ciclos de trabajo de agentes, no un flujo exclusivo de desarrollo de software. El agente host ejecuta la tarea con su propio modelo, herramientas, conectores, memoria y runtime. El Core no asume un dominio, proveedor de modelos ni tipo de artefacto.

## Modelo de dominio

Cada sesión debe conservar:
- Objetivo y contexto autorizado.
- Dominio/tipo de tarea como etiqueta descriptiva, no como restricción.
- Criterios obligatorios y preferencias.
- Presupuesto de iteraciones, tiempo y recursos.
- Resultados por iteración, evidencias, errores y decisiones de recuperación.
- Estado final y criterios pasados, fallidos o no verificables.

La evaluación se especializa mediante plugins. El Core aplica lifecycle, límites, persistencia y convergencia; no intenta resolver con una única rúbrica problemas de investigación, análisis, redacción, planificación, software, datos, operaciones y creatividad.

## Componentes

- Core: ciclo acotado, estados, límites y convergencia.
- Task contract: objetivo, contexto, criterios y presupuesto.
- Agent contract: frontera normalizada entre motor y agente.
- Adapters: traducen APIs, CLI o SDK nativos al contrato.
- Evaluators: verifican resultados con evidencia adecuada al dominio.
- Skills: experiencia e instrucciones reutilizables en los hosts.
- MCP Server: expone operaciones, recursos y prompts.
- Plugins: entry points Python para agentes y evaluadores.
- Storage: journal SQLite; otros stores implementarán la misma interfaz.
- Host recipes: guías para Claude Code, Codex, OpenCode, Cursor y otros.

## Modos de uso

1. In-agent: el host ejecuta la tarea y usa ADAPTIX para estructurar el ciclo y, opcionalmente, registrar el historial vía MCP.
2. Delegated: el Core invoca agentes mediante adapters instalados.

## Evaluación y convergencia

La evaluación debe ser específica al dominio. Por ejemplo, investigación requiere calidad y corroboración de fuentes; escritura requiere precisión y adecuación a audiencia; análisis requiere supuestos y cálculos reproducibles; software puede usar tests. No se debe imponer una métrica común ni declarar criterios obligatorios satisfechos sin evidencia.

## Límites de confianza

Los paquetes de adaptadores y evaluadores ejecutan código dentro del proceso y deben ser confiables. Las salidas externas se consideran datos no confiables. El Core nunca debe inferir permisos a partir de las capacidades declaradas por un agente. Acciones destructivas, financieras o externas necesitan autorización explícita.

## Puntos de extensión

- Entry points: loop_maker.agents y loop_maker.evaluators.
- Contratos en src/loop_maker/contracts.py.
- Skills canónicas en skills/.
- Herramientas MCP en src/loop_maker/mcp_server.py.

## Capability selection and host execution boundary

Capability discovery, deterministic selection and optional ranking identify suitable candidates; they do not invoke them. For host-native capabilities, the host remains responsible for resolving interface references, revalidating permissions and availability immediately before invocation, and executing through its existing runtime.

The selection result is a decision record, not a callable or execution grant. Delegated AgentAdapters remain a separate, trusted extension path. See [Capability Selection and Host Execution Boundary](capability-host-execution-contract-v1.md) for the normative lifecycle, failure semantics and security requirements.

The host-mediated handoff, binding resolution and decision-correlated outcome journal are design targets; they are not yet implemented as an end-to-end runtime flow.
