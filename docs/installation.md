# Instalación y experiencia de uso

Loop Maker se utiliza desde el agente que ya empleas. No instala un agente nuevo ni cambia el proveedor de modelos. La instalación añade skills e instrucciones al proyecto; MCP es opcional y aporta persistencia de sesiones y herramientas compartidas.

## Linux / macOS

Instalación directa:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.sh)
```

Instalación en otra carpeta:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.sh) --target /ruta/al/proyecto
```

Para probar una rama:

```bash
LOOP_MAKER_BRANCH=feat/agent-agnostic-orchestrator \
  bash <(curl -fsSL https://raw.githubusercontent.com/thewild001/loop-maker/feat/agent-agnostic-orchestrator/bootstrap.sh) \
  --target /ruta/al/proyecto
```

Desde un checkout:

```bash
bash scripts/install-skills.sh --target /ruta/al/proyecto
```

## Windows PowerShell

```powershell
$installer = "https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.ps1"
Invoke-RestMethod $installer | Invoke-Expression
```

Para especificar destino o rama:

```powershell
$script = Invoke-RestMethod "https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.ps1"
Invoke-Expression $script -Target "C:\\ruta\\al\\proyecto" -Branch "main"
```

Para instalar la rama de desarrollo, sustituye main por feat/agent-agnostic-orchestrator.

## Uso desde el agente

Abre el proyecto en un host compatible e invoca:
- `/loop-maker`: ciclo principal multipropósito.
- `/loop-maker-diagnostics`: diagnóstico y recuperación.
- `/loop-maker-autoimprove`: mejora controlada.
- `/loop-maker-stress-test`: pruebas de límites y escenarios adversos.

La skill principal adapta los criterios de evaluación al dominio: investigación, análisis, redacción, planificación, software, datos, operaciones o trabajo creativo. Sin MCP funciona en modo in-agent, pero no dispone de persistencia propia de sesiones.

## MCP opcional

Consulta [MCP por host](../integrations/mcp/README.md). Durante esta fase, instala el extra MCP desde un checkout local; no presupongas que el paquete ya está publicado en PyPI.

## Seguridad

- Los archivos existentes se preservan por defecto.
- `--force` / `-Force` permite reemplazar los archivos instalados por Loop Maker.
- El instalador no edita la configuración MCP del host.
- Revisa los cambios antes de utilizarlo en repositorios o espacios de trabajo sensibles.
