# Integración con Cursor

Cursor puede consumir servidores MCP y reglas de proyecto. Instala la guía del orquestador como regla:

```bash
mkdir -p .cursor/rules
cp integrations/cursor/loop-maker.mdc .cursor/rules/loop-maker.mdc
```

Registra loop-maker-mcp en la configuración MCP de Cursor utilizando el transporte stdio soportado. Mantén las skills canónicas en el repositorio para reutilizarlas con otros agentes.
