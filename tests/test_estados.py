import pytest

from aula.dominio.estados import (TRANSICIONES, PlanInmutable, TransicionInvalida,
                                  transicionar, transiciones_validas)
from aula.dominio.modelos import EstadoMatricula, Matricula


def matricula(estado, plan="PLAN-2024"):
    return Matricula(estudiante_id="EST-0001", curso_academico="2026-2027",
                     plan_aplicado=plan, version_plan_aplicada="1.2.0", estado=estado)

def test_pasar_solicitada_a_validada():
    """Comprueba que la matricula en estado solicitada puede pasar a validada.
    cubre: SPEC-001/A-03
    """
    m = matricula(EstadoMatricula.SOLICITADA)
    resultado = transicionar(m,EstadoMatricula.VALIDADA)    
    assert resultado.estado == EstadoMatricula.VALIDADA


def test_solicitada_no_puede_pasar_a_cerrada():
    """Una transicion no permitida lanza TransicionInvalida.

    cubre: SPEC-001/A-03
    """
    m = matricula(EstadoMatricula.SOLICITADA)
    with pytest.raises(TransicionInvalida):
        transicionar(m, EstadoMatricula.CERRADA)


def test_anulada_es_estado_final():
    """Desde un estado final no se puede transicionar a ningun otro.

    cubre: SPEC-001/A-03
    """
    m = matricula(EstadoMatricula.ANULADA)
    with pytest.raises(TransicionInvalida):
            transicionar(m, EstadoMatricula.SOLICITADA)

def test_solicitada_puede_cambiar_de_plan():
    """Antes de confirmar, la matricula puede cambiar de plan.

    cubre: SPEC-001/INV-03
    """
    m = matricula(EstadoMatricula.SOLICITADA)
    resultado = transicionar(m, EstadoMatricula.VALIDADA, nuevo_plan= "PLAN-2025")
    assert resultado.estado == EstadoMatricula.VALIDADA and resultado.plan_aplicado == "PLAN-2025"


def test_confirmada_no_puede_cambiar_de_plan():
    """Una matricula confirmada no puede cambiar de plan.

    cubre: SPEC-001/INV-03
    """
    m = matricula(EstadoMatricula.CONFIRMADA)
    with pytest.raises(PlanInmutable):
        transicionar(m, EstadoMatricula.EN_CURSO,nuevo_plan= "PLAN-2025")

def test_en_curso_no_puede_cambiar_de_plan():
    """Un estado posterior a confirmada tampoco puede cambiar de plan.

    cubre: SPEC-001/INV-03
    """
    m = matricula(EstadoMatricula.EN_CURSO)
    with pytest.raises(PlanInmutable):
        transicionar(m, EstadoMatricula.CALIFICADA,nuevo_plan= "PLAN-2025")


def test_confirmada_con_mismo_plan_no_es_cambio():
    """Pasar el mismo plan que ya tiene no cuenta como cambio (decision P5).

    cubre: SPEC-001/INV-03
    """
    m = matricula(EstadoMatricula.CONFIRMADA)
    resultado = transicionar(m, EstadoMatricula.EN_CURSO, nuevo_plan="PLAN-2024")
    assert resultado.estado == EstadoMatricula.EN_CURSO


def test_cambio_de_plan_rechazado_no_modifica_la_matricula():
    """Si se rechaza el cambio de plan, la matricula queda intacta.

    cubre: SPEC-001/INV-03
    """
    m = matricula(EstadoMatricula.CONFIRMADA)
    with pytest.raises(PlanInmutable):
        transicionar(m, EstadoMatricula.EN_CURSO, nuevo_plan="PLAN-2025")
    assert m.estado == EstadoMatricula.CONFIRMADA
    assert m.plan_aplicado == "PLAN-2024"


def test_transiciones_validas_devuelve_copia():
    """Modificar lo que devuelve transiciones_validas no altera el grafo.

    cubre: SPEC-001/A-03
    """
    destinos = transiciones_validas(EstadoMatricula.CERRADA)
    destinos.add(EstadoMatricula.SOLICITADA)
    assert TRANSICIONES[EstadoMatricula.CERRADA] == set()


def test_todos_los_estados_estan_en_el_grafo():
    """Todos los estados de EstadoMatricula tienen entrada en TRANSICIONES.

    cubre: SPEC-001/A-03
    """
    for estado in EstadoMatricula:
        assert estado in TRANSICIONES


