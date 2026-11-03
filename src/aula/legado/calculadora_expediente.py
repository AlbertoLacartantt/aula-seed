"""Calculadora de expediente: refactor de calculadora_expediente_v1.

Mismo comportamiento que el legado, incluidos los dos no documentados de los que
depende la ordenacion de becas, pero calculado en Decimal (invariante 2 de CLAUDE.md).
Las diferencias con el legado estan declaradas en DESVIACIONES.md.
Lo llama el proceso nocturno de secretaria.
"""

import json
from decimal import ROUND_HALF_UP, Decimal

NOTA_CONVALIDADA = Decimal("5.0")
DOS_DECIMALES = Decimal("0.01")
MAX_CONVOCATORIAS = 6
_CACHE = {}


def _redondear(valor):
    return valor.quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)


def cargar_plan(ruta):
    with open(ruta, encoding="utf-8") as fichero:
        plan = json.load(fichero)
    return plan, {a["codigo"]: a for a in plan["asignaturas"]}


def _creditos(mapa, codigo):
    return mapa[codigo]["creditos"] if codigo in mapa else 0


def _codigos(expediente):
    """Codigos de asignatura en el orden en que aparecen, sin repetir."""
    return list(dict.fromkeys(r["codigo_asignatura"] for r in expediente["registros"]))


def _registros_de(expediente, codigo):
    return [r for r in expediente["registros"] if r["codigo_asignatura"] == codigo]


def _es_convalidada(registros):
    return any(r["estado"] == "convalidada" for r in registros)


def _superada(registros):
    return any(r["estado"] in ("aprobada", "convalidada") for r in registros)


def _nota_que_cuenta(registros):
    """Nota del aprobado de mayor convocatoria, o None si no hay."""
    aprobados = [r for r in registros if r["estado"] == "aprobada"]
    if not aprobados:
        return None
    nota = max(aprobados, key=lambda r: r["convocatoria"]).get("nota")
    return None if nota is None else Decimal(str(nota))


def media(expediente, mapa):
    numerador = Decimal(0)
    denominador = 0
    for codigo in _codigos(expediente):
        creditos = _creditos(mapa, codigo)
        if creditos == 0:
            continue
        registros = _registros_de(expediente, codigo)
        if _es_convalidada(registros):
            # No documentado 1: suma en el numerador con nota fija y no en el denominador.
            numerador += NOTA_CONVALIDADA * creditos
            continue
        nota = _nota_que_cuenta(registros)
        if nota is None:
            continue
        # No documentado 2: se redondea por asignatura, antes de acumular.
        numerador += _redondear(nota) * creditos
        denominador += creditos
    if denominador == 0:
        return Decimal("0.00")
    return _redondear(numerador / denominador)


def creditos_superados(expediente, mapa):
    return sum(
        _creditos(mapa, codigo)
        for codigo in _codigos(expediente)
        if _superada(_registros_de(expediente, codigo))
    )


def progreso(expediente, plan, mapa):
    total = plan["creditos_titulo"]
    if total == 0:
        return Decimal("0.00")
    return _redondear(Decimal(creditos_superados(expediente, mapa) * 100) / total)


def convocatorias(expediente):
    cuenta = {}
    for r in expediente["registros"]:
        if r["estado"] != "convalidada":
            cuenta[r["codigo_asignatura"]] = cuenta.get(r["codigo_asignatura"], 0) + 1
    return cuenta


def puede_matricular(expediente, codigo):
    return convocatorias(expediente).get(codigo, 0) < MAX_CONVOCATORIAS


def calcular(expediente, ruta_plan):
    """Punto de entrada del proceso nocturno. Cachea por estudiante y plan."""
    clave = expediente["estudiante_id"] + "|" + ruta_plan
    if clave not in _CACHE:
        plan, mapa = cargar_plan(ruta_plan)
        _CACHE[clave] = {
            "estudiante_id": expediente["estudiante_id"],
            "nota_media": media(expediente, mapa),
            "creditos_superados": creditos_superados(expediente, mapa),
            "progreso_pct": progreso(expediente, plan, mapa),
        }
    return _CACHE[clave]


def calcular_lote(expedientes, ruta_plan):
    return [calcular(e, ruta_plan) for e in expedientes]
