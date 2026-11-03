# Arquitectura

## Principio

Loop Maker orquesta el ciclo de iteración. El agente conectado realiza el trabajo con su propio modelo, herramientas, memoria y runtime. Los proveedores de modelos no forman parte del contrato del Core.

## Componentes

- Core: loop acotado, estados, convergencia y presupuestos.
- Agent Contract: frontera normalizada entre motor y agente.
- Adapters: traducen APIs, CLI o SDK nativos al contrato.
- Skills: instrucciones reutilizables cargadas por los hosts.
- MCP Server: expone operaciones Loop Maker como herramientas y recursos.
- Plugins: entry points Python en loop_maker.agents.
- Storage: journal SQLite; otros stores implementarán la misma interfaz.
- Host recipes: guías delgadas para Claude Code, Codex, OpenCode, Cursor y otros.

## Límites de confianza

Los paquetes de adaptadores ejecutan código dentro del proceso y deben ser confiables. La salida de agentes externos se considera dato no confiable. Las herramientas MCP solo deben exponerse a clientes locales autorizados o clientes autenticados. El Core nunca debe inferir permisos a partir de las capacidades declaradas por un agente.

## Convergencia

El motor aplica comprobaciones básicas deterministas (éxito, finalización y salida no vacía). Cuando hay criterios obligatorios, exige un Evaluator independiente que devuelva criterios verificados, fallidos y evidencia específica por criterio. Una puntuación LLM por sí sola no satisface criterios obligatorios.

## Puntos de extensión

- Grupo de entry points Python: loop_maker.agents y loop_maker.evaluators.
- Protocolo AgentAdapter en src/loop_maker/contracts.py.
- Skills canónicas en skills/.
- Herramientas MCP en src/loop_maker/mcp_server.py.
