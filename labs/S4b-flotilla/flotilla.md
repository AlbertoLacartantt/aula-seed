# Flotilla de Aula

Tres agentes deterministas sobre el mismo servidor MCP. El contrato validable está en
`agentes/flotilla/contrato.json`; este fichero lo dibuja.

```mermaid
flowchart LR
    MCP[(Servidor MCP<br/>agentes/mcp_aula/servidor.py)]

    C[Conformidad<br/>agentes/conformidad/agente.py]
    T[Triaje<br/>agentes/triaje/agente.py]
    M[Modernización<br/>agentes/modernizacion/agente.py]
    H((Humano))

    C -- obtener_spec --> MCP
    T -- resultado_tests, listar_specs, trazabilidad --> MCP
    M -- resultado_tests --> MCP

    C -- "spec y criterios cubiertos" --> T
    T -- "ficheros de src/ con criterios en riesgo" --> M
    M -- "propuesta (nadie la aplica)" --> H

    C -. escribe .-> CJ[ciclo/conformidad.json]
    T -. escribe .-> TJ[ciclo/triaje.json]
    M -. escribe .-> MJ[ciclo/modernizacion.json]
```

## Handoff

| De | A | Qué se pasa |
|----|---|-------------|
| Conformidad | Triaje | La spec y los criterios que el PR cubre, para comprobar que sus tests pasan |
| Triaje | Modernización | Los ficheros de `src/` de la spec cuyos criterios están en riesgo |
| Modernización | Humano | La propuesta de mejora; ningún agente la aplica |

Cada agente solo lee del servidor MCP y escribe solo en su fichero de `ciclo/`.

## Conflicto

- **Prevención:** ningún agente modifica `src/`, `tests/` ni `specs/`, y cada uno escribe solo
  en su propio fichero de salida, así que no pueden pisarse.
- **Si dos señalan el mismo fichero:** no se aplica ningún cambio y decide el humano.
