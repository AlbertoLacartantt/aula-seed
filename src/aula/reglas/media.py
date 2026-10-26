"""S2: resolver SPEC-002 antes de implementar el calculo del expediente."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from ..dominio.modelos import EstadoRegistro, Expediente, Plan
from . import motor

DOS_DECIMALES = Decimal("0.01")


def nota_media_ponderada(expediente: Expediente, plan: Plan) -> Decimal:
    """Media ponderada por creditos, redondeada una sola vez al final (CA-01, CA-04, CA-07)."""
    suma = Decimal(0)
    creditos = 0
    for asignatura in plan.asignaturas.values():
        nota = _nota_que_cuenta(expediente.registros_de(asignatura.codigo))
        if nota is None:
            continue
        suma += nota * asignatura.creditos
        creditos += asignatura.creditos
    if creditos == 0:
        return Decimal("0.00")
    return (suma / creditos).quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)


def _nota_que_cuenta(registros: list):
    """Ninguna si esta convalidada (A-02); si no, la del aprobado de mayor convocatoria (A-01)."""
    if any(es_convalidada(r) for r in registros):
        return None
    aprobados = [r for r in registros if r.estado is EstadoRegistro.APROBADA]
    if not aprobados:
        return None
    return max(aprobados, key=lambda r: r.convocatoria).nota


def creditos_superados(expediente: Expediente, plan: Plan) -> int:
    """Aprobadas y convalidadas, cada asignatura una vez (CA-05). Misma regla que SPEC-001."""
    return motor.creditos_superados(expediente, plan)


def progreso(expediente: Expediente, plan: Plan) -> Decimal:
    """Porcentaje de creditos superados sobre los del titulo, con dos decimales (CA-06)."""
    porcentaje = Decimal(creditos_superados(expediente, plan) * 100) / plan.creditos_titulo
    return porcentaje.quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)


def convocatorias_por_asignatura(expediente: Expediente, plan: Plan) -> dict:
    """Convocatorias consumidas de cada asignatura con registros. La convalidacion no consume."""
    return {asignatura.codigo: expediente.convocatorias_consumidas(asignatura.codigo)
            for asignatura in plan.asignaturas.values()
            if expediente.registros_de(asignatura.codigo)}


def resumen_expediente(expediente: Expediente, plan: Plan) -> dict:
    """Respuesta de la consulta de expediente."""
    return {
        "estudiante_id": expediente.estudiante_id,
        "nota_media": nota_media_ponderada(expediente, plan),
        "creditos_superados": creditos_superados(expediente, plan),
        "progreso": progreso(expediente, plan),
        "convocatorias": convocatorias_por_asignatura(expediente, plan),
    }


def es_convalidada(registro) -> bool:
    """Un registro convalidado no cuenta para la nota media (CA-03)."""
    return registro.estado is EstadoRegistro.CONVALIDADA