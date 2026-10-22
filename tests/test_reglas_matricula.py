from dataclasses import replace

import pytest

from aula import auditoria
from aula.reglas.motor import (Grupo, VentanaCerrada, VentanaMatricula,
                               creditos_pendientes, creditos_superados,
                               evaluar_solicitud, ordenar_por_prioridad)
from tests.utilidades import expediente, plan, registro, solicitud

VENTANA = VentanaMatricula(inicio="2026-09-01T00:00:00", fin="2026-09-30T23:59:59")


@pytest.fixture(autouse=True)
def traza_temporal(tmp_path, monkeypatch):
    """Cada test escribe la auditoria en un fichero propio y vacio."""
    monkeypatch.setattr(auditoria, "RUTA_TRAZA", tmp_path / "traza.jsonl")


def evaluar(codigos, exp=None, p=None, grupos=None, momento="2026-09-10T10:00:00"):
    return evaluar_solicitud(solicitud(codigos, momento=momento), exp or expediente(),
                             p or plan(), VENTANA, grupos or {})


def linea(matricula, codigo):
    return next(l for l in matricula.lineas if l.codigo_asignatura == codigo)


def test_momento_anterior_al_inicio():
    """Un momento anterior al inicio esta fuera de la ventana.

    cubre: SPEC-001/CA-01
    """
    assert not VENTANA.contiene("2026-08-31T23:59:59")


def test_instante_exacto_de_inicio_esta_dentro():
    """La ventana es inclusiva: el instante de inicio cuenta como dentro.

    cubre: SPEC-001/CA-01
    """
    assert VENTANA.contiene("2026-09-01T00:00:00")


def test_instante_exacto_de_fin_esta_dentro():
    """La ventana es inclusiva: el instante de fin cuenta como dentro.

    cubre: SPEC-001/CA-01
    """
    assert VENTANA.contiene("2026-09-30T23:59:59")


def test_grupo_con_plazas_esta_libre():
    """Un grupo con ocupacion por debajo de la capacidad tiene plaza.

    cubre: SPEC-001/CA-05
    """
    assert Grupo(codigo_asignatura="MAT101", capacidad=30, ocupadas=29).libre


def test_fuera_de_ventana_rechaza_la_solicitud_completa():
    """Fuera de ventana se lanza VentanaCerrada y queda auditado.

    cubre: SPEC-001/CA-01
    """
    with pytest.raises(VentanaCerrada):
        evaluar(["MAT101"], momento="2026-10-01T00:00:00")
    assert auditoria.leer_traza()[0]["resultado"] == {"error": "ventana cerrada"}


def test_prerrequisito_pendiente_rechaza_solo_esa_linea():
    """La linea con prerrequisito pendiente se rechaza y el resto sigue.

    cubre: SPEC-001/CA-02
    """
    m = evaluar(["EST101", "PRG101"])
    assert linea(m, "EST101").motivo_rechazo == "prerrequisitos pendientes: MAT101"
    assert linea(m, "PRG101").admitida


def test_limite_de_creditos_admite_en_orden_de_solicitud():
    """Se admite en orden hasta el limite y se rechaza lo que no cabe.

    cubre: SPEC-001/CA-03
    """
    m = evaluar(["PRG101", "MAT101", "FIS101"], p=replace(plan(), limite_creditos_curso=15))
    assert linea(m, "PRG101").admitida and linea(m, "MAT101").admitida
    assert linea(m, "FIS101").motivo_rechazo == "limite de creditos superado"


def test_excepcion_fin_de_carrera_con_pendientes_igual_al_umbral():
    """Con 12 pendientes (igual al umbral) el limite pasa a ser 12.

    cubre: SPEC-001/CA-03
    """
    p = replace(plan(), limite_creditos_curso=6)
    superadas = [registro(c, "aprobada", 7) for c in p.asignaturas
                 if c not in ("MOV301", "SEG301")]
    m = evaluar(["MOV301", "SEG301"], exp=expediente(*superadas), p=p)
    assert m.creditos_admitidos == 12


def test_convocatorias_agotadas_rechaza_la_linea():
    """Con el maximo de convocatorias consumidas la linea se rechaza.

    cubre: SPEC-001/CA-04
    """
    suspensos = [registro("MAT101", "suspensa", 2, convocatoria=n) for n in range(1, 7)]
    m = evaluar(["MAT101"], exp=expediente(*suspensos))
    assert linea(m, "MAT101").motivo_rechazo == "convocatorias agotadas"


def test_convalidacion_no_consume_convocatoria():
    """Una convalidacion no suma convocatorias consumidas.

    cubre: SPEC-001/CA-04
    """
    regs = [registro("MAT101", "suspensa", 2, convocatoria=n) for n in range(1, 6)]
    exp = expediente(*regs, registro("MAT101", "convalidada"))
    assert exp.convocatorias_consumidas("MAT101") == 5


def test_grupo_completo_deja_la_linea_en_espera_sin_consumir_creditos():
    """Grupo lleno: linea en espera, no gasta limite y el resto continua.

    cubre: SPEC-001/CA-05
    """
    grupos = {"PRG101": Grupo("PRG101", capacidad=10, ocupadas=10)}
    m = evaluar(["PRG101", "MAT101"], p=replace(plan(), limite_creditos_curso=6),
                grupos=grupos)
    assert linea(m, "PRG101").en_espera and not linea(m, "PRG101").admitida
    assert linea(m, "MAT101").admitida


def test_convalidadas_cuentan_como_superadas():
    """Los creditos convalidados cuentan como superados.

    cubre: SPEC-001/CA-06
    """
    exp = expediente(registro("MAT101", "aprobada", 7), registro("PRG101", "convalidada"))
    assert creditos_superados(exp, plan()) == 15
    assert creditos_pendientes(exp, plan()) == 192 - 15


def test_suspenso_y_aprobado_cuentan_una_sola_vez():
    """Varios registros de la misma asignatura no duplican sus creditos.

    cubre: SPEC-001/CA-06
    """
    exp = expediente(registro("MAT101", "suspensa", 3),
                     registro("MAT101", "aprobada", 6, convocatoria=2))
    assert creditos_superados(exp, plan()) == 6


def test_ordenar_por_creditos_y_despues_por_momento():
    """Mas creditos primero; a igualdad, la solicitud mas temprana.

    cubre: SPEC-001/CA-07
    """
    tarde = solicitud(["EST101"], momento="2026-09-10T12:00:00", estudiante="A")
    pronto = solicitud(["EST101"], momento="2026-09-10T09:00:00", estudiante="B")
    nuevo = solicitud(["MAT101"], momento="2026-09-01T00:00:00", estudiante="C")
    expedientes = {"A": expediente(registro("MAT101", "aprobada", 5), estudiante="A"),
                   "B": expediente(registro("MAT101", "aprobada", 5), estudiante="B")}
    ordenadas = ordenar_por_prioridad([nuevo, tarde, pronto], expedientes, plan())
    assert [s.estudiante_id for s in ordenadas] == ["B", "A", "C"]


def test_asignatura_ya_superada_se_rechaza():
    """Pedir una asignatura ya aprobada rechaza esa linea.

    cubre: SPEC-001/CA-08
    """
    m = evaluar(["MAT101"], exp=expediente(registro("MAT101", "aprobada", 8)))
    assert linea(m, "MAT101").motivo_rechazo == "asignatura ya superada"


def test_toda_evaluacion_escribe_una_auditoria_con_el_plan():
    """Una evaluacion, una entrada de auditoria con codigo y version de plan.

    cubre: SPEC-001/INV-01
    """
    evaluar(["MAT101"])
    traza = auditoria.leer_traza()
    assert len(traza) == 1
    assert (traza[0]["plan"], traza[0]["version_plan"]) == ("PLAN-2024", "1.2.0")


def test_una_linea_por_codigo_solicitado():
    """Nunca se pierde ni se duplica una linea, aunque haya rechazos.

    cubre: SPEC-001/INV-02
    """
    codigos = ["MAT101", "EST101", "NOEXISTE", "PRG101"]
    m = evaluar(codigos)
    assert [l.codigo_asignatura for l in m.lineas] == codigos


def test_solicitud_con_duplicados_se_rechaza():
    """Una lista con duplicados no se evalua.

    cubre: SPEC-001/A-08
    """
    with pytest.raises(ValueError):
        evaluar(["MAT101", "MAT101"])


def test_prerrequisito_prevalece_sobre_grupo_completo():
    """Grupo completo y prerrequisito pendiente: rechazo, no espera.

    cubre: SPEC-001/CA-05
    """
    m = evaluar(["PRG102"], grupos={"PRG102": Grupo("PRG102", 10, 10)})
    assert not linea(m, "PRG102").en_espera
    assert linea(m, "PRG102").motivo_rechazo == "prerrequisitos pendientes: PRG101"
