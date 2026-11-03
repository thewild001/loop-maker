# Ejecutar el servidor MCP con Docker

Loop Maker puede ejecutarse en un contenedor Docker usando el transporte MCP **stdio**. El contenedor no expone puertos: el cliente MCP inicia Docker y mantiene stdin/stdout abiertos.

## Requisitos

- Docker Engine o Docker Desktop con soporte para Docker Compose.
- Un cliente MCP que permita configurar un comando stdio.

## Construir la imagen

Desde la raíz del repositorio:

```bash
docker build -t loop-maker-mcp:local .
```

## Configurar un cliente MCP

El patrón recomendado es ejecutar el contenedor de forma interactiva, sin TTY y eliminándolo al cerrar el cliente. La base SQLite se conserva en un volumen Docker:

```json
{
  "mcpServers": {
    "loop-maker": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "LOOP_MAKER_DB=/data/loop-maker.sqlite3",
        "-v", "loop-maker-data:/data",
        "loop-maker-mcp:local"
      ]
    }
  }
}
```

Crea el volumen una sola vez si todavía no existe:

```bash
docker volume create loop-maker-data
```

Esta configuración JSON puede adaptarse a clientes como Claude Code, Cursor y otros que acepten servidores MCP stdio. En Codex, el bloque equivalente en `~/.codex/config.toml` es:

```toml
[mcp_servers.loop-maker]
command = "docker"
args = [
  "run", "--rm", "-i",
  "-e", "LOOP_MAKER_DB=/data/loop-maker.sqlite3",
  "-v", "loop-maker-data:/data",
  "loop-maker-mcp:local"
]
```

En Windows, utiliza el mismo comando Docker; asegúrate de que Docker Desktop esté iniciado y que el cliente pueda encontrar el ejecutable `docker`.

## Docker Compose

El repositorio incluye `compose.yaml` con volumen persistente y stdin habilitado. Para adjuntar un cliente MCP manualmente:

```bash
docker compose build
docker compose run --rm -T loop-maker-mcp
```

Este comando sirve para comprobar el arranque y conectar manualmente stdin/stdout. Para la integración cotidiana con un cliente MCP, utiliza la configuración `docker run -i` anterior.

No ejecutes el servicio en segundo plano (`up -d`): stdio es un canal entre el cliente y el proceso, no un endpoint de red.

## Persistencia y seguridad

- La base de datos se almacena en `/data/loop-maker.sqlite3`; monta un volumen en `/data` para conservar sesiones entre reinicios.
- La imagen ejecuta el proceso como usuario no privilegiado `loopmaker` (UID 10001).
- No se publica ningún puerto ni se habilita transporte HTTP.
- No montes el socket Docker dentro del contenedor.
- Los adapters y evaluadores instalados son código ejecutable: incorpora únicamente plugins confiables en una imagen derivada y revisa sus dependencias.
- La imagen no contiene herramientas externas ni agentes LLM; el adapter `demo` sigue siendo una fixture de prueba.

## Diagnóstico

Si el cliente informa que el servidor MCP se desconectó:

1. Verifica que la imagen exista con `docker image inspect loop-maker-mcp:local`.
2. Prueba el comando con `docker run --rm -i loop-maker-mcp:local`.
3. Comprueba que el cliente no esté asignando un TTY ni ejecutando Docker en modo detached.
4. Verifica permisos y disponibilidad del volumen persistente.

El transporte stdio requiere que stdout quede reservado para los mensajes del protocolo MCP. No agregues mensajes de inicio, banners ni logs a stdout.
