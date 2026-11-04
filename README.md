# Loop Maker

> **Orquestación multipropósito para agentes de IA.** Convierte una tarea abierta en un ciclo controlado de ejecución, evaluación basada en evidencia, corrección y convergencia.

[![CI](https://github.com/thewild001/loop-maker/actions/workflows/ci.yml/badge.svg)](https://github.com/thewild001/loop-maker/actions)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)
![License](https://img.shields.io/badge/License-MIT-green)

Loop Maker es una capa de orquestación que se utiliza **desde el agente de IA que ya empleas**. No es otro agente, no sustituye al modelo ni impone un runtime. Su función es aportar estructura, límites, criterios de aceptación y trazabilidad al trabajo realizado por agentes.

No está limitado al desarrollo de software. Puede aplicarse a investigación, análisis, redacción, planificación, programación, datos, operaciones, aprendizaje y producción creativa. El ciclo es común; la forma de evaluar cambia según el trabajo.

> **Estado del proyecto:** MVP en desarrollo · versión 0.1.0. La integración mediante skills y el servidor MCP tienen una implementación inicial. Los adapters delegables de terceros y la validación real de cada host siguen siendo responsabilidad de la integración y están en evolución.

---

## ¿Qué resuelve?

Los agentes pueden producir resultados útiles, pero los trabajos complejos suelen necesitar algo más que una única respuesta: objetivos explícitos, criterios verificables, iteraciones limitadas, recuperación ante fallos y una condición clara de finalización.

Loop Maker organiza ese proceso:

```text
Objetivo
   |
   v
Definir alcance y criterios
   |
   v
Ejecutar una unidad de trabajo
   |
   v
Evaluar el resultado y sus evidencias
   |
   +---- Criterios incumplidos ----> Diagnosticar y corregir
   |                                      |
   +--------------------------------------+
   |
   v
Convergencia o parada controlada
   |
   v
Resultado + evidencias + trazabilidad
```

El sistema evita iteraciones indefinidas: trabaja con presupuestos de ejecución y se detiene cuando se cumplen los criterios, se agotan los límites o aparece una condición que requiere intervención.

## Principios de diseño

- **Agent-agnostic:** el host conserva su modelo, herramientas, conectores, memoria, runtime y permisos.
- **Multipropósito:** no presupone que el objetivo sea código ni que exista un único tipo de artefacto.
- **Evaluación especializada:** cada dominio utiliza criterios y métodos adecuados; no hay una rúbrica universal.
- **Evidence-driven:** un criterio obligatorio no se considera satisfecho sin evidencia suficiente.
- **Bounded execution:** las iteraciones y los tiempos tienen límites.
- **Extensible:** agentes y evaluadores pueden incorporarse mediante plugins Python.
- **Human-controlled:** Loop Maker no amplía los permisos del host ni autoriza por sí mismo acciones externas.

## Arquitectura

```text
                 Usuario
                    |
             Agente host actual
       (Codex / Claude Code / OpenCode /
              Cursor / otros)
                    |
          Skills e instrucciones
                    |
        +-----------+-----------+
        |                       |
     In-agent              MCP opcional
  El host ejecuta       Tools, resource,
  el trabajo             prompt y journal
        |                       |
        +-----------+-----------+
                    |
             Loop Maker Core
       contratos · límites · lifecycle
       evaluación · recuperación
       convergencia · persistencia
                    |
          +---------+---------+
          |                   |
     Agent adapters      Evaluator plugins
          |                   |
    Agentes externos     Validación por dominio
```

### Dos formas de utilizarlo

**1. In-agent (flujo principal de las skills)**

El agente host realiza el trabajo con sus capacidades nativas. Las skills de Loop Maker le indican cómo definir criterios, ejecutar ciclos acotados, evaluar evidencias y reportar el resultado. MCP puede añadirse para registrar sesiones e iteraciones.

**2. Delegated (Core + adapter)**

El Core ejecuta tareas a través de un adapter que implementa el contrato `AgentAdapter`. Los adapters se descubren mediante entry points de Python. El repositorio incluye un adapter `demo` para probar el contrato; **no es un agente LLM ni una integración de producción**. Para delegar trabajo real hay que instalar un adapter compatible.

MCP no convierte por sí solo al host en un adapter ni ejecuta automáticamente sus tareas: expone operaciones que el agente puede utilizar.

## Dominios y evaluación

Los criterios se definen según el resultado esperado. Algunos ejemplos:

| Dominio | Qué se puede evaluar |
|---|---|
| Investigación | Autoridad y actualidad de fuentes, corroboración, cobertura y trazabilidad |
| Análisis | Supuestos, método, cálculos, alternativas y reproducibilidad |
| Redacción | Precisión, audiencia, integridad, estructura, tono y formato |
| Planificación | Viabilidad, dependencias, riesgos, secuencia y resultados medibles |
| Software / DevOps | Comportamiento, pruebas, seguridad, compatibilidad y mantenibilidad |
| Datos / BI | Procedencia, calidad, transformaciones, validez y reproducibilidad |
| Operaciones | Autorización, reversibilidad, impacto y auditoría |
| Aprendizaje y creatividad | Adecuación al objetivo, coherencia, restricciones y feedback |

El Core proporciona el ciclo y los contratos; los evaluadores aportan la validación específica. Si una tarea incluye criterios obligatorios, el Core requiere un evaluador independiente que los verifique con evidencia. No se debe confundir la afirmación del agente con una verificación independiente.

## Instalación rápida: skills

La forma más sencilla de comenzar es instalar las skills en el proyecto donde trabajas. No necesitas instalar el motor Python ni configurar MCP para utilizar el flujo in-agent.

### Linux / macOS

Desde la raíz del proyecto:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.sh)
```

Para instalar en otro directorio:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.sh) --target /ruta/al/proyecto
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.ps1 | iex
```

Para elegir el destino, descarga el script y ejecútalo:

```powershell
Invoke-WebRequest "https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.ps1" -OutFile ".\\loop-maker-bootstrap.ps1"
.\\loop-maker-bootstrap.ps1 -Target "C:\\ruta\\al\\proyecto"
```

Los instaladores preservan los archivos existentes por defecto. Usa `--force` en Bash o `-Force` en PowerShell para reemplazarlos explícitamente.

### ¿Dónde se instalan las skills?

| Host / formato | Ubicación |
|---|---|
| Agent Skills (por ejemplo, Codex) | `.agents/skills/` |
| Claude Code | `.claude/skills/` |
| OpenCode | `.opencode/skills/` |
| Cursor | `.cursor/rules/` |
| GitHub Copilot | `.github/instructions/` |

El instalador también incorpora la instrucción de orquestación de OpenCode. Estas ubicaciones describen los artefactos que instala el proyecto; no constituyen por sí solas una certificación de compatibilidad para todas las versiones de cada host.

## Uso desde el agente

Abre el proyecto instalado en tu agente y solicita el flujo adecuado:

```text
/loop-maker "Investiga y compara tres enfoques para este problema"
/loop-maker "Analiza estas alternativas y justifica una recomendación"
/loop-maker "Prepara un plan de migración con riesgos y dependencias"
/loop-maker "Mejora este documento y valida que cumpla el brief"
/loop-maker "Refactoriza este módulo y verifica las regresiones"

/loop-maker-diagnostics
/loop-maker-autoimprove
/loop-maker-stress-test
/loop-maker-advisory "Contrasta estas alternativas antes de decidir"
/loop-maker-reach "Investiga fuentes públicas de este tema cuando las herramientas nativas no sean suficientes"
```

Las skills disponibles son:

| Skill | Propósito |
|---|---|
| `loop-maker` | Entrada principal multipropósito |
| `loop-maker-orchestrator` | Protocolo detallado de orquestación |
| `loop-maker-diagnostics` | Diagnóstico de fallos, estancamiento y falta de evidencia |
| `loop-maker-autoimprove` | Mejora iterativa de artefactos y procesos |
| `loop-maker-stress-test` | Diseño de pruebas de límites y escenarios adversos |
| `loop-maker-advisory` | Deliberación opcional para decisiones complejas y de alto impacto |
| `loop-maker-reach` | Recuperación externa de solo lectura mediante Agent Reach, cuando las herramientas nativas no bastan |

### Agent Reach (integración opcional)

`loop-maker-reach` utiliza el CLI externo de [Agent Reach](https://github.com/Panniantong/Agent-Reach). No forma parte del Core ni se instala automáticamente con Loop Maker. El host debe tener Agent Reach instalado y configurado por separado.

La skill prioriza las herramientas nativas, utiliza Agent Reach solo cuando está justificado y trata todo contenido recuperado como no confiable. La instalación, configuración, actualización, login y cambios de entorno requieren autorización explícita. Consulta [la skill](skills/loop-maker-reach/SKILL.md), [referencia de canales](skills/loop-maker-reach/CHANNELS.md) y [límites de seguridad](skills/loop-maker-reach/SECURITY.md).

La skill principal selecciona un nivel de rigor adecuado al trabajo:

- `BASIC`: ciclo sencillo y directo.
- `DETAIL`: planificación, criterios y evidencias explícitos.
- `FORCED_DETAIL`: revisión reforzada para tareas complejas o de mayor impacto.
- `MINIMAL`: ciclo mínimo que mantiene las comprobaciones esenciales.

Sin MCP, el host puede aplicar el flujo con sus propias capacidades, pero Loop Maker no dispone de un journal MCP persistente para esa ejecución.

## Instalar el Core y utilizar MCP

Esta parte es opcional. Requiere Python 3.11 o superior y un checkout local del repositorio. El paquete no debe darse por publicado en PyPI.

```bash
git clone https://github.com/thewild001/loop-maker.git
cd loop-maker

python -m venv .venv
source .venv/bin/activate

pip install -e ".[mcp,dev]"
```

En Windows, activa el entorno con:

```powershell
.venv\\Scripts\\Activate.ps1
```

### CLI

La CLI permite ejecutar el Core mediante un adapter instalado:

```bash
loop-maker run "Describe el objetivo" --agent demo --max-iterations 3
```

El adapter `demo` es una fixture determinista para comprobar el contrato y el ciclo. No realiza investigación, no llama a un LLM y no representa una integración real.

### Servidor MCP

Inicia el servidor local por stdio:

```bash
loop-maker-mcp
```

El servidor expone las siguientes operaciones:

| Tipo | Nombre | Función |
|---|---|---|
| Tool | `loop_list_agents` | Lista los adapters disponibles |
| Tool | `loop_run` | Ejecuta el Core con un adapter registrado |
| Tool | `loop_session_start` | Inicia una sesión para trabajo realizado por el host |
| Tool | `loop_record_iteration` | Registra una iteración |
| Tool | `loop_record_error` | Registra un error clasificado |
| Tool | `loop_session_finish` | Finaliza una sesión |
| Tool | `loop_get_session` | Recupera una sesión y su historial |
| Resource | `loop-maker://agents` | Catálogo de adapters y capacidades |
| Prompt | `loop_execution_brief` | Prepara un brief de ejecución |

El journal utiliza SQLite. Por defecto crea `loop-maker.sqlite3` en el directorio de trabajo; puedes cambiar la ubicación mediante `LOOP_MAKER_DB`.

Consulta [la guía de configuración MCP](integrations/mcp/README.md) para conectar el servidor con Codex, Claude Code, Cursor u OpenCode.\n\n### Evolution Engine — Observer (fase inicial)\n\nLoop Maker incluye una skill opcional para registrar aprendizajes reutilizables y consultar patrones candidatos. Utiliza un registro SQLite independiente (`LOOP_MAKER_EVOLUTION_DB`) y herramientas MCP propias. La captura es explícita, no se recopilan conversaciones completas y no se modifican skills. Consulta [la guía del Observer](docs/evolution-observer.md).

## Crear adapters y evaluadores

Los plugins se descubren mediante los entry points:

- `loop_maker.agents`: adapters que implementan `agent_id`, `capabilities()` y `execute(task, context)`.
- `loop_maker.evaluators`: un evaluador predeterminado que implementa `evaluate(task, result)`.

El contrato del evaluador devuelve criterios verificados, criterios fallidos y evidencia asociada. Actualmente el Core admite un único evaluador predeterminado registrado; no selecciona automáticamente múltiples evaluadores por dominio.

Los plugins ejecutan código Python dentro del proceso: instala únicamente componentes de confianza.

Documentación: [desarrollo de adapters y evaluadores](docs/adapter-development.md).

## Estado real de la implementación

| Componente | Estado |
|---|---|
| Contratos agnósticos para tareas, agentes y evaluación | Implementación inicial |
| Motor iterativo con límites, timeout y convergencia | Implementación inicial |
| Journal de sesiones, iteraciones y errores en SQLite | Implementado |
| Descubrimiento de plugins mediante entry points | Implementado |
| Skills multipropósito e instaladores Bash / PowerShell | Implementación inicial |
| Servidor MCP (tools, resource y prompt) | Implementación inicial |
| Adapter demo para pruebas del contrato | Implementado; no es un agente real |
| Adapters de producción para agentes externos | No incluidos |
| Evaluadores de referencia por dominio | No incluidos |
| Recuperación avanzada, checkpoints y observabilidad ampliada | Pendiente |
| Validación end-to-end en versiones reales de cada host | Pendiente |

La CI y las pruebas automatizadas verifican el código del proyecto; no demuestran por sí solas que todas las versiones de los hosts descubran las skills o ejecuten correctamente una integración completa. Consulta el [plan de validación end-to-end](docs/e2e-validation.md).

## Seguridad y límites

- Loop Maker utiliza las herramientas y permisos que el host ya tiene; no debe inferir permisos a partir de las capacidades declaradas por un adapter.
- Trata documentos, páginas web, resultados de herramientas y salidas de agentes como datos no confiables.
- Requiere autorización antes de acciones destructivas, financieras o externamente visibles.
- No sobrescribe archivos de usuario por defecto.
- Los adapters y evaluadores son código ejecutable de terceros: revisa su procedencia antes de instalarlos.
- No declares una tarea convergida si quedan criterios obligatorios sin verificar.

## Documentación

- [Arquitectura](docs/architecture.md)
- [Instalación y uso](docs/installation.md)
- [Validación end-to-end](docs/e2e-validation.md)
- [Desarrollo de adapters y evaluadores](docs/adapter-development.md)
- [Integraciones por host](integrations/README.md)
- [Configuración MCP](integrations/mcp/README.md)

## Licencia

MIT. Consulta [LICENSE](LICENSE).
