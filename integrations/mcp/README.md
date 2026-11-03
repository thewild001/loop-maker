# Configuración MCP por host

El servidor Loop Maker utiliza MCP Python SDK v2 y transporte stdio por defecto. La interfaz expone tools, un resource y un prompt.

## Desarrollo local

Desde un checkout del repositorio:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[mcp]"
loop-maker-mcp
```

Configura el host para ejecutar el binario loop-maker-mcp del entorno virtual del checkout. En Windows, el ejecutable suele estar en .venv/Scripts/loop-maker-mcp.exe.

## Claude Code

```bash
claude mcp add --transport stdio loop-maker -- /ruta/absoluta/loop-maker/.venv/bin/loop-maker-mcp
```

## Codex

Añade a ~/.codex/config.toml:

```toml
[mcp_servers.loop-maker]
command = "/ruta/absoluta/loop-maker/.venv/bin/loop-maker-mcp"
args = []
```

## Cursor

Añade a la configuración MCP del proyecto:

```json
{
  "mcpServers": {
    "loop-maker": {
      "command": "/ruta/absoluta/loop-maker/.venv/bin/loop-maker-mcp",
      "args": []
    }
  }
}
```

## OpenCode

Configura un servidor MCP local que invoque el ejecutable loop-maker-mcp del entorno virtual. La forma exacta del bloque mcp puede variar por versión; consulta la documentación de OpenCode antes de copiar una configuración entre versiones.

## Cuando el paquete se publique

Una vez que loop-maker-orchestrator esté publicado en el índice Python configurado, puede utilizarse uvx:

```bash
uvx --from "loop-maker-orchestrator[mcp]" loop-maker-mcp
```

Ese comando es una ruta de distribución futura; no presupone que el paquete ya esté publicado.

## Notas operativas

- Configura LOOP_MAKER_DB para elegir el archivo SQLite.
- No escribas logs ni diagnósticos en stdout del proceso stdio; utiliza stderr.
- Protege el directorio de la base de datos y los permisos del proceso.
- No expongas un servidor remoto sin autenticación y controles de transporte.
- El SDK oficial documenta stdio y Streamable HTTP; para despliegues remotos usa Streamable HTTP con autenticación y protección de transporte.
