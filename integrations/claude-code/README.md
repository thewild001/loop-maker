# Integración con Claude Code

Instala las skills compartidas en .claude/skills:

```bash
mkdir -p .claude/skills
cp -R skills/* .claude/skills/
```

Registra el servidor MCP mediante el comando o configuración stdio soportado por la versión de Claude Code instalada. El paquete local expone:

```bash
uvx --from "loop-maker-orchestrator[mcp]" loop-maker-mcp
```

Las skills son instrucciones portables; MCP proporciona herramientas y acceso a sesiones. Confirma los parámetros de configuración con la documentación de la versión que utilizas.
