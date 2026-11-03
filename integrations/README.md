# Integraciones de agentes

Loop Maker distribuye un paquete canónico de Agent Skills y un servidor MCP opcional. Las integraciones son adaptadores delgados: cargan las mismas skills y conectan el host al mismo servidor MCP.

| Host | Skills / instrucciones | MCP |
|---|---|---|
| Codex y hosts compatibles con Agent Skills | .agents/skills/ | Configuración MCP del host |
| Claude Code | .claude/skills/ | MCP stdio |
| OpenCode | .opencode/skills/ y .opencode/agents/ | Configuración MCP del host |
| Cursor | .cursor/rules/ | Configuración MCP del host |
| Otros agentes | Directorio Agent Skills o instrucciones del sistema | stdio / Streamable HTTP |

Estas recetas son guías de integración, no certificaciones oficiales. Valida el formato de configuración soportado por la versión concreta del host antes de automatizar su instalación.
