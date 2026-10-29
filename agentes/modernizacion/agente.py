"""Agente de modernizacion, determinista: analiza un modulo sin ejecutarlo ni modificarlo y propone mejoras."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

from agentes.mcp_aula.servidor import resultado_tests

RAIZ = Path(__file__).resolve().parents[2]


def _hallazgos(arbol: ast.Module) -> list:
    usados = {
        n.id for n in ast.walk(arbol) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
    }
    hallazgos = []
    for nodo in arbol.body:
        if isinstance(nodo, ast.FunctionDef) and nodo.name not in usados:
            hallazgos.append((nodo.lineno, "nombre_sin_uso", nodo.name))
        if isinstance(nodo, ast.Assign):
            for destino in nodo.targets:
                if isinstance(destino, ast.Name) and destino.id not in usados:
                    hallazgos.append((nodo.lineno, "nombre_sin_uso", destino.id))
    for funcion in (n for n in arbol.body if isinstance(n, ast.FunctionDef)):
        for nodo in ast.walk(funcion):
            if (
                isinstance(nodo, ast.Constant)
                and type(nodo.value) in (int, float)
                and nodo.value not in (0, 1)
            ):
                hallazgos.append((nodo.lineno, "numero_magico", str(nodo.value)))
            if (
                isinstance(nodo, ast.Call)
                and isinstance(nodo.func, ast.Name)
                and nodo.func.id == "float"
            ):
                hallazgos.append((nodo.lineno, "coma_flotante", "float(): CLAUDE.md pide Decimal"))
    return [
        {"linea": linea, "tipo": tipo, "detalle": detalle}
        for linea, tipo, detalle in sorted(hallazgos)
    ]


def _caracterizacion(ruta: Path) -> dict:
    importa = re.compile(r"^\s*(?:from|import)\s.*\b%s\b" % re.escape(ruta.stem), re.M)
    tests = sorted(
        t.relative_to(RAIZ).as_posix()
        for t in (RAIZ / "tests").rglob("test_*.py")
        if importa.search(t.read_text(encoding="utf-8"))
    )
    verde = bool(tests) and all(resultado_tests({"ruta": t}).get("verde") for t in tests)
    return {"tests": tests, "verde": verde}


def proponer(ruta_modulo: str) -> dict:
    ruta = (RAIZ / ruta_modulo).resolve()
    if ruta.suffix != ".py" or not ruta.is_file() or not ruta.is_relative_to(RAIZ):
        return {"error": "%s no es un modulo .py del proyecto" % ruta_modulo}
    caracterizacion = _caracterizacion(ruta)
    if not caracterizacion["tests"]:
        motivo = "no hay tests de caracterizacion del modulo: no se puede tocar (regla dura S5)"
    elif not caracterizacion["verde"]:
        motivo = "los tests del modulo no estan en verde: no se puede tocar"
    else:
        motivo = "los tests del modulo estan en verde: se puede aplicar con la red puesta"
    return {
        "modulo": ruta_modulo,
        "caracterizacion": caracterizacion,
        "se_puede_aplicar": caracterizacion["verde"],
        "motivo": motivo,
        "hallazgos": _hallazgos(ast.parse(ruta.read_text(encoding="utf-8"))),
    }


def principal(argv=None):
    parser = argparse.ArgumentParser(description="Agente de modernizacion")
    parser.add_argument("--modulo", required=True)
    args = parser.parse_args(argv)
    propuesta = proponer(args.modulo)
    print(json.dumps(propuesta, ensure_ascii=False, indent=2))
    return 1 if "error" in propuesta else 0


if __name__ == "__main__":
    raise SystemExit(principal())
