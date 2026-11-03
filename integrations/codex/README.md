# Integración con Codex y hosts compatibles con Agent Skills

Instala las skills en el directorio de proyecto .agents/skills:

```bash
mkdir -p .agents/skills
cp -R skills/* .agents/skills/
```

Registra loop-maker-mcp en la configuración MCP del host:

```bash
uvx --from "loop-maker-orchestrator[mcp]" loop-maker-mcp
```

Codex y otros hosts compatibles pueden cargar el mismo paquete sin mantener una variante específica de cada proveedor.
