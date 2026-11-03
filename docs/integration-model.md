# Modelo de integración

Loop Maker ofrece dos modalidades que se complementan y no deben confundirse.

## 1. In-agent (skills + MCP journal)

El host agent carga la skill Loop Maker y realiza el trabajo con sus propias herramientas. El MCP server proporciona estado durable:

1. loop_session_start antes de iniciar el ciclo.
2. El host ejecuta una iteración con su runtime nativo.
3. loop_record_iteration registra salida, aceptación y usage conocido.
4. Si ocurre un error, loop_record_error registra código y evidencia.
5. El host repite únicamente si existe una hipótesis de mejora.
6. loop_session_finish registra el estado terminal.
7. loop_get_session permite recuperar el historial.

En este modo Loop Maker no invoca al agente host desde dentro. El host está ejecutando el workflow.

## 2. Delegated (Core + adapter plugin)

Una aplicación externa llama a loop_run. El Core selecciona un adapter registrado y lo invoca mediante AgentAdapter.execute. Este modo sí permite que Loop Maker orqueste agentes externos.

Los adapters se distribuyen como paquetes Python independientes y se registran mediante el grupo de entry points loop_maker.agents.

## Seguridad y permisos

Un MCP client que puede llamar loop_run puede iniciar ejecuciones en los adapters instalados. Expón únicamente adapters de confianza, limita los permisos del proceso y no publiques un servidor stdio/HTTP sin controles de autorización apropiados. Las capacidades declaradas son informativas; no constituyen permisos.
