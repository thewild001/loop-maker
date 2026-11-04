# Instalación y experiencia de uso

ADAPTIX se utiliza desde el agente que ya empleas. No instala un agente nuevo ni cambia el proveedor de modelos. La instalación añade skills e instrucciones al proyecto; MCP es opcional y aporta persistencia de sesiones y herramientas compartidas. Los comandos y nombres de skills conservan el prefijo histórico `loop-maker` durante la transición para no romper instalaciones existentes.

## Linux / macOS

Instalación desde la rama principal:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.sh)
```

Instalación en otra carpeta:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.sh) --target /ruta/al/proyecto
```

Desde un checkout:

```bash
bash scripts/install-skills.sh --target /ruta/al/proyecto
```

## Windows PowerShell

Instala directamente:

```powershell
irm https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.ps1 | iex
```

Para especificar destino, descarga y ejecuta el script:

```powershell
Invoke-WebRequest "https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.ps1" -OutFile ".\loop-maker-bootstrap.ps1"
.\loop-maker-bootstrap.ps1 -Target "C:\ruta\al\proyecto"
```

## Uso desde el agente

Abre el proyecto en un host compatible e invoca:
- `/loop-maker`: ciclo principal multipropósito.
- `/loop-maker-diagnostics`: diagnóstico y recuperación.
- `/loop-maker-autoimprove`: mejora controlada.
- `/loop-maker-stress-test`: pruebas de límites y escenarios adversos.

La skill principal adapta los criterios de evaluación al dominio: investigación, análisis, redacción, planificación, software, datos, operaciones o trabajo creativo. Sin MCP funciona en modo in-agent, pero no dispone de persistencia propia de sesiones.

## MCP opcional

Consulta [MCP por host](../integrations/mcp/README.md). Instala el extra MCP desde un checkout local; no presupongas que el paquete ya está publicado en PyPI. La distribución Python y el módulo de importación conservan sus nombres históricos (`loop-maker-orchestrator` y `loop_maker`).

## Seguridad

- Los archivos existentes se preservan por defecto.
- `--force` / `-Force` permite reemplazar los archivos instalados por ADAPTIX.
- El instalador no edita la configuración MCP del host.
- Revisa los cambios antes de utilizarlo en repositorios o espacios de trabajo sensibles.
