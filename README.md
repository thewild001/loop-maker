# Loop Maker Orchestrator

> Orquestación multipropósito de ciclos de trabajo para agentes de IA: investigar, analizar, escribir, planificar, programar, procesar datos, operar herramientas y crear.

**Estado:** MVP en desarrollo · **Versión:** 0.1.0 · **Python:** 3.11+

## Propósito

Loop Maker no es un framework exclusivamente de programación ni un agente que sustituye a otros. Es una capa de orquestación que se utiliza desde el agente que el usuario ya emplea, de forma similar a la experiencia de MentorKit, pero con otro propósito: convertir tareas abiertas en ciclos acotados de ejecución, evaluación, corrección y convergencia.

Se aplica a investigación, análisis, redacción, planificación, desarrollo de software, datos, operaciones, aprendizaje y producción creativa. El método es común; los criterios de evaluación cambian según el dominio.

## Experiencia de uso

Instala las skills en el proyecto y abre ese proyecto con tu agente habitual.

### Linux / macOS

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.sh)
```

Para instalar en otra carpeta:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.sh) --target /ruta/al/proyecto
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.ps1 | iex
```

Para especificar destino, descarga el script y ejecútalo:

```powershell
Invoke-WebRequest https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.ps1 -OutFile .\loop-maker-bootstrap.ps1
.\loop-maker-bootstrap.ps1 -Target "C:\ruta\al\proyecto"
```

Los archivos existentes se preservan por defecto; `--force` / `-Force` permite reemplazar archivos administrados por Loop Maker.

Después invoca la skill desde un host compatible:

```text
/loop-maker "Investiga y compara tres enfoques para este problema"
/loop-maker "Prepara un plan de migración con riesgos y dependencias"
/loop-maker "Analiza estos datos y valida las conclusiones"
/loop-maker "Refactoriza este módulo y verifica que no haya regresiones"
/loop-maker-diagnostics
/loop-maker-autoimprove
/loop-maker-stress-test
```

La instalación habilita el modo in-agent. El servidor MCP es opcional y aporta herramientas comunes e historial persistente.

## Cómo funciona

```text
Usuario
  |
Agente host (Codex / Claude Code / OpenCode / Cursor / ...)
  | skills                   | MCP opcional
  +-------------+-------------+
                |
         LOOP MAKER CORE
    objetivo · criterios · ciclos
    evaluación · recuperación
    convergencia · journal
                |
      Agent adapters / plugins
                |
       runtimes y herramientas
```

- **In-agent:** el host ejecuta la tarea con sus herramientas; Loop Maker estructura y controla el ciclo.
- **Delegated:** el Core invoca un agente mediante un adapter/plugin registrado.
- **Skills:** proporcionan la experiencia de invocación desde los hosts.
- **MCP:** expone operaciones de ciclo, recursos y persistencia.

El Core no selecciona el modelo ni asume que la tarea sea código. El host conserva sus permisos, conectores, herramientas y runtime.

## Evaluación según el dominio

| Dominio | Ejemplos de criterios |
|---|---|
| Investigación | calidad, actualidad, corroboración y trazabilidad de fuentes |
| Análisis | supuestos, método, cálculos, alternativas y reproducibilidad |
| Redacción | precisión, audiencia, integridad, tono y formato |
| Planificación | viabilidad, dependencias, riesgos y resultados medibles |
| Software | comportamiento, pruebas, seguridad y mantenibilidad |
| Datos | procedencia, calidad, transformaciones y validez |
| Operaciones | autorización, reversibilidad, impacto y auditoría |
| Creatividad | fidelidad al brief, coherencia, restricciones y feedback |

No existe un único evaluador universal que sirva para todos estos casos. Loop Maker define contratos extensibles para incorporar evaluadores adecuados a cada tipo de tarea. Los criterios obligatorios no deben declararse satisfechos sin evidencia.

## Instalación del motor y MCP

Desde el checkout:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[mcp,dev]"
loop-maker-mcp
```

Consulta [integrations/mcp/README.md](integrations/mcp/README.md) para configurar el host. Sin MCP, la skill sigue siendo utilizable; no habrá persistencia propia de sesiones.

## Skills

| Skill | Responsabilidad |
|---|---|
| `loop-maker` | Entrada principal multipropósito |
| `loop-maker-orchestrator` | Protocolo de orquestación |
| `loop-maker-diagnostics` | Diagnóstico y recuperación |
| `loop-maker-autoimprove` | Mejora iterativa de resultados y procesos |
| `loop-maker-stress-test` | Pruebas de límites y escenarios adversos |

## Estado de implementación

| Capacidad | Estado |
|---|---|
| Core iterativo, contratos y journal SQLite | Implementación inicial |
| Skills e instalador Bash/PowerShell | Implementación inicial |
| MCP tools/resources/prompts | Implementación inicial |
| Plugins de agentes vía entry points | Implementado |
| Adapters nativos delegables para hosts | Pendiente |
| Evaluadores de referencia por dominio | Pendiente |
| Recuperación avanzada y checkpoints | Pendiente |
| Métricas y observabilidad avanzadas | Pendiente |

Las integraciones actuales son una base para el uso in-agent, no una certificación de compatibilidad de extremo a extremo para cada host. El proyecto no se considera listo para producción hasta completar pruebas reales por host, evaluadores y hardening.

## Documentación

- [Instalación y uso](docs/installation.md)
- [Arquitectura](docs/architecture.md)
- [Desarrollo de adapters](docs/adapter-development.md)
- [Integraciones](integrations/README.md)
- [MCP por host](integrations/mcp/README.md)

MIT License.
