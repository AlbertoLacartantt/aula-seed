"""Caracterizacion del modulo heredado calculadora_expediente_v1.

Fija lo que el legado HACE hoy, no lo que deberia hacer. Los valores esperados
salen de ejecutarlo. Es la red del refactor de S5: si un test cambia, el
comportamiento ha cambiado.
"""

import pytest

from aula.legado import calculadora_expediente_v1 as legado
from tests.utilidades import RAIZ

RUTA_PLAN = str(RAIZ / "datos" / "planes" / "PLAN-2024.json")
PLAN, MAPA = legado.cargar_plan(RUTA_PLAN)


def reg(codigo, estado, nota=None, convocatoria=1):
    return {
        "codigo_asignatura": codigo,
        "estado": estado,
        "nota": nota,
        "convocatoria": convocatoria,
    }


def exp(*registros, estudiante="EST-T"):
    return {"estudiante_id": estudiante, "registros": list(registros)}


@pytest.fixture(autouse=True)
def cache_vacia():
    legado._CACHE.clear()


def test_media_ponderada_por_creditos():
    expediente = exp(reg("MAT101", "aprobada", 7.0), reg("PRG101", "aprobada", 8.0))
    assert legado.media(expediente, MAPA) == 7.6


def test_no_documentado_1_convalidada_suma_en_numerador_pero_no_en_denominador():
    expediente = exp(reg("MAT101", "aprobada", 7.0), reg("FIS101", "convalidada"))
    # (7*6 + 5.0*6) / 6: la convalidada infla la media, que pasa de 10
    assert legado.media(expediente, MAPA) == 12.0


def test_no_documentado_2_redondeo_por_asignatura_antes_de_acumular():
    expediente = exp(reg("MAT101", "aprobada", 5.0), reg("PRG101", "aprobada", 5.006))
    # 5.006 se redondea a 5.01 antes de ponderar; con redondeo final daria 5.00
    assert legado.media(expediente, MAPA) == 5.01


def test_cuenta_el_aprobado_de_mayor_convocatoria_no_la_mejor_nota():
    expediente = exp(reg("MAT101", "aprobada", 9.0, 1), reg("MAT101", "aprobada", 6.0, 2))
    assert legado.media(expediente, MAPA) == 6.0


def test_ignora_suspensas_aprobadas_sin_nota_y_asignaturas_fuera_del_plan():
    expediente = exp(
        reg("MAT101", "suspensa", 3.0),
        reg("XXX999", "aprobada", 10.0),
        reg("ING101", "aprobada", None),
        reg("PRG101", "aprobada", 8.0),
    )
    assert legado.media(expediente, MAPA) == 8.0


def test_sin_notas_que_cuenten_la_media_es_cero():
    assert legado.media(exp(), MAPA) == 0.0
    assert legado.media(exp(reg("FIS101", "convalidada")), MAPA) == 0.0


def test_creditos_superados_cuenta_aprobadas_y_convalidadas_una_vez():
    expediente = exp(
        reg("MAT101", "aprobada", 7.0),
        reg("MAT101", "aprobada", 8.0, 2),
        reg("FIS101", "convalidada"),
        reg("PRG101", "suspensa", 2.0),
    )
    assert legado.creditos_superados(expediente, MAPA) == 12


def test_progreso_es_porcentaje_sobre_creditos_del_titulo():
    expediente = exp(reg("MAT101", "aprobada", 7.0), reg("FIS101", "convalidada"))
    assert legado.progreso(expediente, PLAN, MAPA) == 6.25


def test_convocatorias_no_cuentan_convalidadas_y_limitan_la_matricula():
    expediente = exp(
        reg("MAT101", "suspensa", 2.0, 1),
        reg("MAT101", "suspensa", 3.0, 2),
        reg("FIS101", "convalidada"),
    )
    assert legado.convocatorias(expediente) == {"MAT101": 2}
    seis = exp(*[reg("MAT101", "suspensa", 2.0, i) for i in range(1, 7)])
    assert legado.puede_matricular(seis, "MAT101") is False
    assert legado.puede_matricular(exp(), "MAT101") is True


def test_calcular_devuelve_el_resumen_y_redondea_en_coma_flotante():
    resultado = legado.calcular(exp(reg("MAT101", "aprobada", 7.0), estudiante="EST-1"), RUTA_PLAN)
    # 6*100/192 = 3.125; el round() de float da 3.12, no 3.13
    assert resultado == {
        "estudiante_id": "EST-1",
        "nota_media": 7.0,
        "creditos_superados": 6,
        "progreso_pct": 3.12,
    }


def test_calcular_cachea_por_estudiante_y_plan_aunque_cambie_el_expediente():
    primero = legado.calcular(exp(reg("MAT101", "aprobada", 7.0), estudiante="EST-2"), RUTA_PLAN)
    segundo = legado.calcular(exp(reg("MAT101", "aprobada", 9.0), estudiante="EST-2"), RUTA_PLAN)
    assert segundo is primero
    assert segundo["nota_media"] == 7.0
