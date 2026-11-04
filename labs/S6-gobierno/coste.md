# Coste por criterio de aceptacion verificado

Medido el 2026-11-04. Criterios verificados: 17 (SPEC-001: 8; SPEC-002: 9).

| Coste | Tokens totales | Tokens por criterio |
|-------|----------------|---------------------|
| Ejecutar los agentes (deterministas, sin LLM) | 0 | 0 |
| Construir: entrada + salida + escritura en cache | 7.729.727 | 454.690 |
| Construir: lectura de cache | 332.439.576 | 19.555.269 |

El coste de construir sale de los logs de Claude Code (`message.usage`) y es un maximo,
porque incluye tambien trabajo que no corresponde a los criterios.
