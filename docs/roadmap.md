# Roadmap de implementación

El roadmap sigue entregas verificables. Los adaptadores nativos se desarrollan después de validar el contrato universal; no se implementan integraciones superficiales que solo cambien el nombre de un prompt.

| Entrega | Objetivo | Estado |
|---|---|---|
| 0.1 Foundation | Core básico, contrato, SQLite, skills, MCP y bootstrap multi-host | En desarrollo |
| 0.2 Contract hardening + host handoff | Evaluadores independientes, límites, cancelación, pruebas de contrato y frontera de ejecución controlada por el host | Contrato de host documentado; runtime pendiente |
| 0.3 Host integrations | Recetas MCP validadas y adapters nativos prioritarios | Pendiente |
| 0.4 Quality & Recovery | Clasificación A-I, circuit breakers, checkpoints y regresiones | Pendiente |
| 0.5 Observability | Métricas, trazas, exportación y retención configurable | Pendiente |
| 0.6 AUTOIMPROVE | Propuestas, benchmarks y promoción con aprobación | Pendiente |
| 0.7 Multi-agent | A2A, delegación y presupuestos por agente | Pendiente |
| 1.0 Production | Seguridad, carga, recuperación, documentación y release | Pendiente |

## Gate 0.1

- Dos agentes distintos pueden conectarse mediante el contrato.
- El Core no importa SDKs de agentes concretos.
- Las skills se instalan sin sobrescribir archivos existentes.
- MCP permite que el host registre sus propias iteraciones.
- SQLite conserva sesiones e historial tras reiniciar el proceso.
- CI ejecuta lint y tests.

## Gate 0.2

- Los criterios obligatorios requieren un Evaluator independiente.
- Un timeout o error del evaluador no produce convergencia falsa.
- Los límites de iteraciones y tiempo se aplican en el Core.
- Los errores A-I tienen política y tests.
- A host can submit its own bounded inventory and receive a selection decision without registering native tools inside ADAPTIX.
- The host resolves and invokes selected capabilities through its own runtime.
- Invocation-time revalidation prevents execution after permission revocation or capability disappearance.
- Selection decisions, invocation outcomes and task-level evaluation remain distinct and correlatable.

## Gate 0.3

Priorizar integraciones por adopción y estabilidad de interfaces. Cada adapter debe tener pruebas de contrato y documentación de capacidades reales. Los hosts que solo consumen Skills/MCP no deben presentarse como adapters delegables.

## Gate 1.0

No se declara producción hasta tener CI verde, cobertura de contrato, pruebas de recuperación, auditoría de permisos MCP y al menos dos integraciones reales independientes.
