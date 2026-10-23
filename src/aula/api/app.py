"""Servicio de arranque. S1 y S2 completan los recursos pendientes."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..dominio.modelos import Expediente, SolicitudMatricula
from ..reglas.motor import VentanaCerrada, VentanaMatricula, evaluar_solicitud
from ..reglas.planes import cargar_plan

app = FastAPI(title="Aula Students", version="0.0.0")

PLAN = cargar_plan("PLAN-2024")
VENTANA = VentanaMatricula(inicio="2026-09-01T00:00:00", fin="2026-09-30T23:59:59")
EXPEDIENTES: dict = {}
MATRICULAS: dict = {}


class SolicitudEntrada(BaseModel):
    estudiante_id: str
    curso_academico: str
    codigos: list[str]
    momento: str | None = None


def _momento(texto: str | None) -> str:
    """Hora local sin zona si falta; 422 si no es ISO-8601 o trae zona (A-13)."""
    if texto is None:
        return datetime.now().isoformat(timespec="seconds")
    try:
        momento = datetime.fromisoformat(texto)
    except ValueError:
        raise HTTPException(status_code=422, detail="momento no es ISO-8601")
    if momento.tzinfo is not None:
        raise HTTPException(status_code=422, detail="momento no debe llevar zona horaria")
    return texto


@app.get("/salud")
def salud():
    return {"estado": "ok", "momento": datetime.now(timezone.utc).isoformat()}


@app.post("/matriculas", status_code=201)
def crear_matricula(entrada: SolicitudEntrada):
    solicitud = SolicitudMatricula(estudiante_id=entrada.estudiante_id,
                                   curso_academico=entrada.curso_academico,
                                   codigos=entrada.codigos,
                                   momento=_momento(entrada.momento))
    expediente = (EXPEDIENTES.get(entrada.estudiante_id)
                  or Expediente(entrada.estudiante_id, PLAN.codigo))
    try:
        matricula = evaluar_solicitud(solicitud, expediente, PLAN, VENTANA, {})
    except VentanaCerrada:
        raise HTTPException(status_code=409, detail="ventana de matricula cerrada")
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    MATRICULAS.setdefault(entrada.estudiante_id, []).append(matricula)
    return asdict(matricula)


@app.get("/expedientes/{estudiante_id}")
def ver_expediente(estudiante_id: str):
    raise HTTPException(status_code=501, detail="S2: consulta de expediente pendiente")
