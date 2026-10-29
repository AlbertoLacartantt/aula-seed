# Bitacora de S4a

Registra iteraciones, hipotesis de mejora y metricas recibidas del mentor.

Comienzo a editar funciones servidor.py 12 , finalizado 13:10

Inicio 15:15 conexcion mcp -fin con prueba realizada 15:50

Agente v1 en el CI (PR #28 y #29)

Qué he añadido:
- En la plantilla de PR, dos líneas: AULA_SPEC_ID y AULA_CRITERIOS. Con ellas cada PR
  dice qué spec implementa y qué criterios. Las dejo como SPEC-nnn y CA-nn para que, si
  no se rellenan, el agente dé error en vez de evaluar contra una spec equivocada.
- En ci.yml, un job "conformidad" que en cada PR lee la descripción, lanza el agente con
  herramientas/conformidad_pr.py y publica el veredicto como comentario en el PR.

Por qué: el entregable pide que el agente publique sus veredictos en PRs reales. Por
ahora el job solo informa, no bloquea: hay PRs que no son de ninguna spec (CI,
bitácoras) y todavía no sé cuánto acierta el agente porque falta la evaluación.

Problemas:
- GitHub guarda la descripción con saltos \r\n y la regex de conformidad_pr.py no
  encajaba. Lo arreglo en el job quitando los \r con tr -d '\r' antes de guardarla.
- La descripción se pasa por una variable de entorno y no directamente en el run, para
  que no se pueda colar un comando escrito en el PR.
- En el PR #28 no salían las líneas nuevas: GitHub coge la plantilla de main, no de la
  rama. Las puse a mano.
- El job se quedó sin el espacio de sangría y YAML lo dejaba fuera de "jobs", así que no
  se ejecutaba. Arreglado en el PR #29. Tenía que haber comprobado el YAML antes de subir.



USERSAD+alacarta@NTTD-FYDSKN3 UCRT64 ~/LaboratorioInicio/aula-seed (feat/evaluacion-conformidad)
$ .venv/Scripts/python.exe -m agentes.conformidad.evaluar --guardar
{
  "fecha": "2026-10-29",
  "casos": 15,
  "matriz": {
    "vp": 1,
    "fp": 0,
    "vn": 5,
    "fn": 9
  },
  "precision": 1.0,
  "recall": 0.1,
  "f1": 0.182,
  "latencia_media_ms": 0.0,
  "coste_usd_por_ejecucion": 0.0,
  "juez": "offline"
}

Casos fallados:
  oro-004: esperado no_conforme_sin_cubrir, obtenido conforme (falso negativo)
  oro-006: esperado no_conforme_sin_cubrir, obtenido conforme (falso negativo)
  oro-007: esperado no_conforme_alcance, obtenido conforme (falso negativo)
  oro-008: esperado no_conforme_alcance, obtenido conforme (falso negativo)
  oro-009: esperado no_conforme_alcance, obtenido conforme (falso negativo)
  oro-010: esperado no_conforme_riesgo, obtenido conforme (falso negativo)
  oro-011: esperado no_conforme_riesgo, obtenido conforme (falso negativo)
  oro-012: esperado no_conforme_riesgo, obtenido conforme (falso negativo)
  oro-013: esperado no_conforme_riesgo, obtenido conforme (falso negativo)

informe guardado en evals\informes\evaluacion-20261029-161152.json

umbrales de S4a: NO SUPERADOS


SERSAD+alacarta@NTTD-FYDSKN3 UCRT64 ~/LaboratorioInicio/aula-seed (feat/evaluacion-conformidad)
$ .venv/Scripts/python.exe -m agentes.conformidad.evaluar --guardar
{
  "fecha": "2026-10-29",
  "casos": 15,
  "matriz": {
    "vp": 9,
    "fp": 0,
    "vn": 5,
    "fn": 1
  },
  "precision": 1.0,
  "recall": 0.9,
  "f1": 0.947,
  "latencia_media_ms": 0.6,
  "coste_usd_por_ejecucion": 0.0,
  "juez": "offline"
}

Casos fallados:
  oro-012: esperado no_conforme_riesgo, obtenido conforme (falso negativo)

informe guardado en evals\informes\evaluacion-20261029-161307.json

umbrales de S4a: SUPERADOS

