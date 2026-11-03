# Configuración MCP por host

El servidor Loop Maker utiliza MCP Python SDK v2 y transporte stdio por defecto. El comando es:

```bash
uvx --from "loop-maker-orchestrator[mcp]" loop-maker-mcp
```

Para desarrollo local desde el repositorio:

```bash
pip install -e ".[mcp]"
loop-maker-mcp
```

## Claude Code

```bash
claude mcp add --transport stdio loop-maker -- uvx --from "loop-maker-orchestrator[mcp]" loop-maker-mcp
```

## Codex

Añade a ~/.codex/config.toml:

```toml
[mcp_servers.loop-maker]
command = "uvx"
args = ["--from", "loop-maker-orchestrator[mcp]", "loop-maker-mcp"]
```

## Cursor

Añade a la configuración MCP del proyecto:

```json
{
  "mcpServers": {
    "loop-maker": {
      "command": "uvx",
      "args": ["--from", "loop-maker-orchestrator[mcp]", "loop-maker-mcp"]
    }
  }
}
```

## OpenCode

La estructura de configuración MCP puede variar según la versión. Consulta la documentación del host y configura un servidor local que ejecute el comando uvx anterior. La receta de skills y perfil de agente está en ../opencode/README.md.

## Notas

- Para una instalación publicada, el paquete debe existir en el índice Python configurado.
- Mientras se desarrolla desde GitHub, instala el paquete desde el checkout editable.
- Configura LOOP_MAKER_DB para elegir el archivo SQLite.
- No escribas logs ni mensajes de diagnóstico en stdout del proceso stdio; utiliza stderr.
- El SDK oficial documenta stdio y Streamable HTTP. Para despliegues remotos, usa Streamable HTTP con autenticación y protección de transporte.
