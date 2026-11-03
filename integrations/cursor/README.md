# Integración con Cursor

Cursor puede consumir servidores MCP y reglas de proyecto. Instala las reglas y skills compartidas:

```bash
bash scripts/install-skills.sh /ruta/al/proyecto
```

Registra loop-maker-mcp en la configuración MCP de Cursor utilizando el transporte stdio soportado. Durante el desarrollo, configura la ruta absoluta al ejecutable del entorno virtual. Consulta ../mcp/README.md.

La regla de Cursor es una entrada delgada; las instrucciones completas permanecen en las skills canónicas.
