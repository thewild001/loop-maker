# Integración con Claude Code

Instala las skills compartidas en .claude/skills:

```bash
bash scripts/install-skills.sh /ruta/al/proyecto
```

Registra el servidor MCP mediante el comando stdio soportado por la versión de Claude Code instalada. Durante el desarrollo, utiliza el ejecutable loop-maker-mcp del entorno virtual del checkout. Consulta ../mcp/README.md para la configuración exacta.

Cuando el paquete esté publicado, podrá utilizarse uvx con el extra mcp.

Las skills son instrucciones portables; MCP proporciona herramientas y acceso a sesiones.
