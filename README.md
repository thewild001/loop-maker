<p align="center">
  <strong>LOOP MAKER</strong><br/>
  <em>Agent-Agnostic Iteration & Orchestration Engine</em>
</p>

# Loop Maker Orchestrator

> Un motor de iteración, evaluación y recuperación para agentes de IA. Independiente de Hermes, OpenCode, Claude Code, Codex, Cursor, Ollama o cualquier proveedor de modelos.

**Estado:** foundation / MVP en desarrollo · **Versión:** 0.1.0 · **Python:** 3.11+

Loop Maker no pretende ser otro framework de agentes. Su responsabilidad es controlar el ciclo de trabajo: definir criterios, gestionar iteraciones, evaluar evidencias, registrar sesiones y detenerse cuando corresponde. El agente conectado conserva sus herramientas, memoria, modelo y runtime.

## Filosofía

- **Skills:** distribuyen el método Loop Maker a los agentes compatibles.
- **MCP:** expone herramientas, recursos y prompts reutilizables.
- **Plugins:** conectan agentes externos mediante un contrato estable.
- **Adapters:** traducen las APIs/CLI/SDK nativas al contrato universal.
- **Core:** mantiene la lógica de iteración independiente de cualquier host.

Hay dos modos complementarios:

1. **In-agent:** el agente activo ejecuta el trabajo con sus propias herramientas y utiliza las skills y herramientas MCP de Loop Maker para registrar y controlar el ciclo.
2. **Delegated:** el Core invoca un agente externo mediante un adapter/plugin registrado.

## Arquitectura

```text
Agent host (Codex / Claude Code / OpenCode / Cursor / ...)
       |                         |
  Agent Skills                 MCP client
       |                         |
       +----------+--------------+
                  |
          LOOP MAKER CORE
       orchestration / lifecycle
       budgets / convergence
       evaluation / recovery
       session journal (SQLite)
                  |
           Agent Adapter API
                  |
        Agent plugins (entry points)
                  |
       Existing agent runtime + tools
```

El Core no selecciona ni administra directamente el LLM del agente. Ollama, OpenAI, Anthropic, Gemini y otros proveedores pertenecen al runtime del agente o a un adapter especializado, no al contrato universal.

## Inicio rápido

### 1. Instalar skills en un proyecto

Desde el repositorio clonado:

```bash
bash scripts/install-skills.sh /ruta/a/tu/proyecto
```

O instalar desde GitHub:

```bash
bash <(curl -fsSL "https://raw.githubusercontent.com/thewild001/loop-maker/main/bootstrap.sh")
```

Para probar la rama de desarrollo actual:

```bash
LOOP_MAKER_BRANCH=feat/agent-agnostic-orchestrator \
  bash <(curl -fsSL "https://raw.githubusercontent.com/thewild001/loop-maker/feat/agent-agnostic-orchestrator/bootstrap.sh")
```

El instalador copia skills a .agents/skills, .claude/skills y .opencode/skills, además de reglas para Cursor y el perfil de orquestador de OpenCode. No modifica archivos de configuración MCP existentes.

### 2. Instalar el motor y el servidor MCP

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[mcp,dev]"
```

En Windows PowerShell, activa .venv\\Scripts\\Activate.ps1.

### 3. Probar el motor

```bash
loop-maker run "Probar el contrato de Loop Maker" --agent demo
```

El adapter demo es una fixture de integración: demuestra el flujo, pero no ejecuta trabajo real ni llama a un LLM.

### 4. Ejecutar el servidor MCP

```bash
loop-maker-mcp
```

Por defecto utiliza transporte stdio y guarda sesiones en loop-maker.sqlite3. La ruta puede configurarse con LOOP_MAKER_DB.

## Skills incluidas

| Skill | Responsabilidad |
|---|---|
| loop-maker-orchestrator | Orquestación y ciclo de convergencia |
| loop-maker | Ejecución iterativa cuando MCP no está disponible |
| loop-maker-diagnostics | Diagnóstico y recuperación de errores |
| loop-maker-autoimprove | Mejora controlada y regresiones |
| loop-maker-stress-test | Pruebas de límites y escenarios adversos |

## Herramientas MCP

- loop_list_agents: descubre adapters instalados.
- loop_run: delega una tarea a un adapter registrado.
- loop_session_start: abre un journal para el agente host.
- loop_record_iteration: persiste una iteración ejecutada por el host.
- loop_record_error: registra errores clasificados A-I.
- loop_session_finish: cierra el ciclo y registra el resultado.
- loop_get_session: recupera la sesión y su historial.

También se expone el recurso loop-maker://agents y el prompt loop_execution_brief.

**Importante:** loop_run utiliza el adapter demo si no se instalan plugins reales. Para el modo in-agent, el agente ejecuta la tarea y usa loop_session_start / loop_record_iteration / loop_session_finish para persistencia. No se debe invocar el adapter demo esperando que sustituya al agente host.

## Integraciones

Consulta [integrations/README.md](integrations/README.md) para Claude Code, Codex, OpenCode, Cursor y hosts compatibles con Agent Skills/MCP.

Las skills y el MCP server ya constituyen la primera vía de integración multi-host. Los adapters nativos para delegar tareas hacia cada producto se incorporarán de forma independiente y solo cuando exista una interfaz soportada y pruebas de contrato. No se declara compatibilidad nativa completa por el mero hecho de que un host pueda consumir MCP.

## Crear un adapter

Los paquetes de terceros registran una factory en el grupo Python entry points loop_maker.agents.

Contrato mínimo:

```python
from loop_maker.contracts import AgentResult, Task

class MyAgentAdapter:
    @property
    def agent_id(self) -> str:
        return "my-agent"

    def capabilities(self) -> dict:
        return {"execute": True, "streaming": False}

    async def execute(self, task: Task, context: dict) -> AgentResult:
        output = await my_agent_sdk.run(task.objective, context=context)
        return AgentResult(output=output, success=True, complete=True)
```

Ver [docs/adapter-development.md](docs/adapter-development.md).

## Desarrollo

```bash
pip install -e ".[dev,mcp]"
make verify
```

## Estado de implementación

| Capacidad | Estado |
|---|---|
| Core iterativo inicial | Implementado en rama de desarrollo |
| Contrato universal Python | Implementado |
| Journal SQLite | Implementado |
| Skills canónicas | Implementadas |
| Instalador multi-host | Implementado |
| MCP tools/resources/prompts | Implementación inicial |
| Registro de plugins Python | Implementado |
| Adapters nativos para hosts populares | Pendiente |
| Contrato de evaluator independiente | Implementado; falta evaluador semántico de referencia |
| Recuperación avanzada / checkpoints | Pendiente |
| PostgreSQL / observabilidad | Pendiente |
| A2A / coordinación multiagente | Pendiente |

La rama inicial no debe considerarse lista para producción hasta que CI, pruebas de contrato, validación de MCP y pruebas de integración por host estén pasando.

## Documentación

- [Arquitectura](docs/architecture.md)
- [Desarrollo de adapters](docs/adapter-development.md)
- [Integraciones](integrations/README.md)

## Licencia

MIT. Ver LICENSE.
