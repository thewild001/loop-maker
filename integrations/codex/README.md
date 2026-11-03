# Integración con Codex y hosts compatibles con Agent Skills

Instala las skills en el directorio de proyecto .agents/skills:

```bash
bash scripts/install-skills.sh /ruta/al/proyecto
```

Registra loop-maker-mcp en la configuración MCP del host. Durante el desarrollo, utiliza la ruta absoluta al ejecutable instalado en el entorno virtual del checkout. Consulta ../mcp/README.md para el ejemplo de config.toml.

Cuando el paquete esté publicado, podrá utilizarse uvx con el extra mcp.

Codex y otros hosts compatibles pueden cargar el mismo paquete sin mantener una variante específica de cada proveedor.
