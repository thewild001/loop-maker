# Integración con OpenCode

Instala las skills canónicas y el perfil del orquestador:

```bash
bash scripts/install-skills.sh /ruta/al/proyecto
```

Para conectar MCP durante el desarrollo, instala el checkout Loop Maker en un entorno virtual y configura el servidor local usando el ejecutable loop-maker-mcp. Consulta ../mcp/README.md para ejemplos y rutas.

Cuando el paquete esté publicado en el índice Python, podrá utilizarse uvx con el extra mcp.

La skill contiene la política del workflow; MCP expone operaciones y persistencia. No dupliques la lógica del orquestador en prompts específicos del host.
