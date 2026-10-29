"""Agente de triaje, determinista: ejecuta los tests y dice que criterios quedan en riesgo."""

from __future__ import annotations

import argparse
import json

from agentes.mcp_aula.servidor import listar_specs, resultado_tests, trazabilidad


def _criterios_por_test() -> dict:
    mapa = {}
    for spec in listar_specs()["specs"]:
        for criterio, tests in trazabilidad({"spec_id": spec["id"]})["cubiertos"].items():
            for test in tests:
                mapa.setdefault(test, []).append("%s/%s" % (spec["id"], criterio))
    return mapa


def diagnosticar(ruta: str = "tests") -> dict:
    resultado = resultado_tests({"ruta": ruta})
    if "error" in resultado:
        return resultado
    mapa = _criterios_por_test()
    fallos = []
    for test in resultado["fallidos"]:
        fichero, _, nombre = test.partition("::")
        clave = "%s::%s" % (fichero.split("/")[-1], nombre.split("[")[0])
        fallos.append({"test": test, "fichero": fichero, "criterios": sorted(mapa.get(clave, []))})
    return {"verde": resultado["verde"], "resumen": resultado["resumen"], "fallos": fallos}


def principal(argv=None):
    parser = argparse.ArgumentParser(description="Agente de triaje")
    parser.add_argument("--ruta", default="tests")
    args = parser.parse_args(argv)
    diagnostico = diagnosticar(args.ruta)
    print(json.dumps(diagnostico, ensure_ascii=False, indent=2))
    return 0 if diagnostico.get("verde") else 1


if __name__ == "__main__":
    raise SystemExit(principal())
