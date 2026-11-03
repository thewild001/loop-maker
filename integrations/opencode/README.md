# Integración con OpenCode

Copia las skills canónicas y el perfil del orquestador:

```bash
mkdir -p .opencode/skills .opencode/agents
cp -R skills/* .opencode/skills/
cp agents/loop-maker-orchestrator.md .opencode/agents/loop-maker-orchestrator.md
```

Registra el servidor MCP en la configuración OpenCode del proyecto usando el formato local/stdio soportado por tu versión. Comando de referencia:

```bash
uvx --from "loop-maker-orchestrator[mcp]" loop-maker-mcp
```

La skill contiene la política de workflow; MCP expone operaciones. No dupliques la lógica de orquestación en prompts específicos del host.
