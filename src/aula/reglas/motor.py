"""S1: implementar las reglas de matricula descritas en SPEC-001."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

from .. import auditoria
from ..dominio.modelos import (EstadoMatricula, Expediente, LineaMatricula,
                               Matricula, Plan, SolicitudMatricula)

MOTIVO_FUERA_DE_PLAN = "no pertenece al plan"
MOTIVO_YA_SUPERADA = "asignatura ya superada"
MOTIVO_PRERREQUISITOS = "prerrequisitos pendientes: %s"
MOTIVO_CONVOCATORIAS = "convocatorias agotadas"
MOTIVO_LIMITE = "limite de creditos superado"


class VentanaCerrada(Exception):
    pass


@dataclass(frozen=True)
class VentanaMatricula:
    inicio: str
    fin: str

    def contiene(self, momento: str) -> bool:
        """Inclusiva en ambos extremos (SPEC-001)."""
        return (datetime.fromisoformat(self.inicio)
                <= datetime.fromisoformat(momento)
                <= datetime.fromisoformat(self.fin))


@dataclass(frozen=True)
class Grupo:
    codigo_asignatura: str
    capacidad: int
    ocupadas: int

    @property
    def libre(self) -> bool:
        """Hay plaza mientras la ocupacion no alcance la capacidad (SPEC-001/CA-05)."""
        return self.ocupadas < self.capacidad


def creditos_superados(expediente: Expediente, plan: Plan) -> int:
    """Aprobadas y convalidadas cuentan (CA-06). Cada asignatura cuenta una vez."""
    return sum(a.creditos for a in plan.asignaturas.values()
               if expediente.superada(a.codigo))


def creditos_pendientes(expediente: Expediente, plan: Plan) -> int:
    return plan.creditos_titulo - creditos_superados(expediente, plan)


def prioridad(expediente: Expediente, plan: Plan) -> int:
    """A mas creditos superados, mas prioridad (CA-07)."""
    return creditos_superados(expediente, plan)


def limite_efectivo(expediente: Expediente, plan: Plan) -> int:
    """Excepcion de fin de carrera de CA-03."""
    pendientes = creditos_pendientes(expediente, plan)
    if pendientes <= plan.umbral_final_carrera:
        return pendientes
    return plan.limite_creditos_curso


def _motivo_rechazo(codigo: str, expediente: Expediente, plan: Plan):
    """Primer motivo de rechazo de la linea, o None. Orden fijado en A-06."""
    if codigo not in plan.asignaturas:
        return MOTIVO_FUERA_DE_PLAN
    if expediente.superada(codigo):
        return MOTIVO_YA_SUPERADA
    pendientes = [p for p in plan.asignatura(codigo).prerrequisitos
                  if not expediente.superada(p)]
    if pendientes:
        return MOTIVO_PRERREQUISITOS % ", ".join(pendientes)
    if expediente.convocatorias_consumidas(codigo) >= plan.max_convocatorias:
        return MOTIVO_CONVOCATORIAS
    return None


def _auditar(solicitud: SolicitudMatricula, plan: Plan, resultado: dict) -> None:
    auditoria.registrar_decision(solicitud.estudiante_id, solicitud.curso_academico,
                                 plan.codigo, plan.version, solicitud.momento, resultado)


def evaluar_solicitud(solicitud: SolicitudMatricula, expediente: Expediente,
                      plan: Plan, ventana: VentanaMatricula,
                      grupos: dict) -> Matricula:
    if not ventana.contiene(solicitud.momento):
        _auditar(solicitud, plan, {"error": "ventana cerrada"})
        raise VentanaCerrada(solicitud.momento)
    if not solicitud.codigos or len(set(solicitud.codigos)) != len(solicitud.codigos):
        _auditar(solicitud, plan, {"error": "solicitud vacia o con duplicados"})
        raise ValueError("la solicitud debe ser no vacia y sin duplicados")

    grupos = grupos or {}
    limite = limite_efectivo(expediente, plan)
    consumidos = 0
    lineas = []
    for codigo in solicitud.codigos:
        creditos = plan.asignaturas[codigo].creditos if codigo in plan.asignaturas else 0
        motivo = _motivo_rechazo(codigo, expediente, plan)
        grupo = grupos.get(codigo)
        if motivo:
            linea = LineaMatricula(codigo, creditos, admitida=False, motivo_rechazo=motivo)
        elif grupo is not None and not grupo.libre:
            linea = LineaMatricula(codigo, creditos, admitida=False, en_espera=True)
        elif consumidos + creditos > limite:
            linea = LineaMatricula(codigo, creditos, admitida=False, motivo_rechazo=MOTIVO_LIMITE)
        else:
            consumidos += creditos
            linea = LineaMatricula(codigo, creditos, admitida=True)
        lineas.append(linea)

    matricula = Matricula(estudiante_id=solicitud.estudiante_id,
                          curso_academico=solicitud.curso_academico,
                          plan_aplicado=plan.codigo, version_plan_aplicada=plan.version,
                          estado=EstadoMatricula.SOLICITADA, lineas=lineas)
    _auditar(solicitud, plan, {"lineas": [asdict(l) for l in lineas]})
    return matricula


def ordenar_por_prioridad(solicitudes: list, expedientes: dict, plan: Plan) -> list:
    """Creditos superados descendente; a igualdad, momento ascendente (CA-07)."""
    def clave(s):
        expediente = expedientes.get(s.estudiante_id) or Expediente(s.estudiante_id, plan.codigo)
        return (-prioridad(expediente, plan), datetime.fromisoformat(s.momento))
    return sorted(solicitudes, key=clave)
