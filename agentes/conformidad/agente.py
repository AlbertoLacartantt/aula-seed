"""Agente v1 de conformidad, determinista: sin LLM, el mismo PR da siempre el mismo veredicto."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from agentes.mcp_aula.servidor import obtener_spec

CONFORME = "conforme"
NO_CONFORME = "no_conforme"

# Separa test en bloques, decorador-defenicion del test-contenido-busca def class o @ y cuando lo encuentra acaba
PATRON_TEST = re.compile(r"((?:^@.*\n)*)^def (test_\w+)\(.*?(?=^@|^def |^class |\Z)", re.M | re.S)


@dataclass
class Veredicto:
    pr: str
    spec: str
    veredicto: str
    criterios_declarados: list = field(default_factory=list)
    criterios_cubiertos: list = field(default_factory=list)
    criterios_sin_cubrir: list = field(default_factory=list)
    fuera_de_alcance: list = field(default_factory=list)
    hallazgos: list = field(default_factory=list)
    explicacion: str = ""

    def a_dict(self):
        return asdict(self)


def _tests(pr: dict) -> list:
    salida = []
    for fichero in pr["ficheros"]:
        if fichero[" "].startswith("tests/"):
            for m in PATRON_TEST.finditer(fichero["contenido"]):
                salida.append({"ruta": fichero["ruta"], "nombre": m.group(2), "texto": m.group(0)})
    return salida


def _sospechoso(texto: str) -> bool:
    if re.search(r"pytest\.mark\.skip|pytest\.skip\(", texto):
        return True
    if re.search(r"^\s*assert\s+True\b", texto, re.M):
        return True
    return "assert" not in texto and "pytest.raises" not in texto


def _cubre(texto: str, spec_id: str) -> list:
    doc = re.search(r'"""(.*?)"""', texto, re.S)
    if not doc:
        return []
    criterios = []
    for etiqueta in re.findall(r"cubre:\s*([^\n]+)", doc.group(1)):
        # La "/" detras del id evita que SPEC-0021 cuente como SPEC-002.
        criterios += re.findall(r"%s/((?:CA|INV)-\d{2})\b" % re.escape(spec_id), etiqueta)
    return criterios


def _rutas(contenido_spec: str) -> list:
    m = re.search(r"^Rutas:\s*(.+)$", contenido_spec, re.M)
    return [r.strip() for r in m.group(1).split(",")] if m else []


def evaluar(pr: dict, spec_id: str, juez=None) -> Veredicto:
    ident = pr.get("id", "sin-id")
    declarados = pr.get("criterios_declarados", [])
    spec = obtener_spec({"id": spec_id})
    if "error" in spec:
        return Veredicto(
            pr=ident,
            spec=spec_id,
            veredicto=NO_CONFORME,
            criterios_declarados=declarados,
            hallazgos=[spec["error"]],
            explicacion=spec["error"],
        )

    cubiertos, hallazgos = set(), []
    for test in _tests(pr):
        if _sospechoso(test["texto"]):
            hallazgos.append("%s::%s no prueba nada" % (test["ruta"], test["nombre"]))
        else:
            cubiertos.update(_cubre(test["texto"], spec_id))
    for criterio in declarados:
        if criterio not in spec["criterios"]:
            hallazgos.append("%s no existe en %s" % (criterio, spec_id))

    sin_cubrir = sorted(set(declarados) - cubiertos)
    rutas = _rutas(spec["contenido"])
    fuera = sorted(f["ruta"] for f in pr["ficheros"] if rutas and f["ruta"] not in rutas)

    resultado = NO_CONFORME if sin_cubrir or fuera or hallazgos else CONFORME
    motivos = []
    if sin_cubrir:
        motivos.append("sin test: " + ", ".join(sin_cubrir))
    if fuera:
        motivos.append("fuera de alcance: " + ", ".join(fuera))
    if hallazgos:
        motivos.append("; ".join(hallazgos))
    return Veredicto(
        pr=ident,
        spec=spec_id,
        veredicto=resultado,
        criterios_declarados=declarados,
        criterios_cubiertos=sorted(cubiertos & set(declarados)),
        criterios_sin_cubrir=sin_cubrir,
        fuera_de_alcance=fuera,
        hallazgos=hallazgos,
        explicacion=" | ".join(motivos) or "todos los criterios declarados tienen test",
    )


def principal(argv=None):
    parser = argparse.ArgumentParser(description="Agente de conformidad v1")
    parser.add_argument("--pr", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    entrada = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    veredicto = evaluar(entrada, args.spec)
    if args.json:
        print(json.dumps(veredicto.a_dict(), ensure_ascii=False, indent=2))
    else:
        print(veredicto.veredicto + ": " + veredicto.explicacion)
    return 1 if veredicto.veredicto == NO_CONFORME else 0


if __name__ == "__main__":
    raise SystemExit(principal())
