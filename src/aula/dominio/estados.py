"""S1: completar las transiciones y proteger el plan confirmado."""
from __future__ import annotations

from .modelos import EstadoMatricula, Matricula

TRANSICIONES: dict[EstadoMatricula, set[EstadoMatricula]] = {
        EstadoMatricula.SOLICITADA: {EstadoMatricula.VALIDADA, EstadoMatricula.ANULADA},
        EstadoMatricula.VALIDADA:  {EstadoMatricula.CONFIRMADA, EstadoMatricula.ANULADA},
        EstadoMatricula.CONFIRMADA: {EstadoMatricula.EN_CURSO},
        EstadoMatricula.EN_CURSO: {EstadoMatricula.CALIFICADA},
        EstadoMatricula.CALIFICADA: {EstadoMatricula.CERRADA},
        EstadoMatricula.CERRADA: set(),
        EstadoMatricula.ANULADA: set()
}


ESTADOS_PLAN_INMUTABLE: set[EstadoMatricula] = {
        EstadoMatricula.CONFIRMADA,
        EstadoMatricula.EN_CURSO,
        EstadoMatricula.CALIFICADA,
        EstadoMatricula.CERRADA
}

class TransicionInvalida(Exception):
    pass


class PlanInmutable(Exception):
    pass


def transiciones_validas(estado: EstadoMatricula) -> set:
    return set(TRANSICIONES.get(estado, set()))


def transicionar(matricula: Matricula, destino: EstadoMatricula,
                 nuevo_plan: str = None) -> Matricula:
    if destino not in transiciones_validas(matricula.estado):
        raise TransicionInvalida(f"{matricula.estado} -> {destino}")

    cambia_plan = nuevo_plan is not None and nuevo_plan != matricula.plan_aplicado

    if cambia_plan and matricula.estado in ESTADOS_PLAN_INMUTABLE:
        raise PlanInmutable("No se puede modificar el plan con la matrícula confirmada o posterior. ")

    matricula.estado = destino
    if cambia_plan:
        matricula.plan_aplicado = nuevo_plan  #FALTA VERSION 
        
    return matricula

