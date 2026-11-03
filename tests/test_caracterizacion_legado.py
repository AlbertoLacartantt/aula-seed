"""Caracterizacion del modulo heredado calculadora_expediente_v1.

Fija lo que el legado HACE hoy, no lo que deberia hacer. Los valores esperados
salen de ejecutarlo. Es la red del refactor de S5: cada test se ejecuta contra
el legado y contra el refactor; si un test cambia, el comportamiento ha cambiado.
"""

from decimal import Decimal

import pytest

from aula.legado import calculadora_expediente as nuevo
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


def dec(valor):
    return Decimal(str(valor))


@pytest.fixture(params=[legado, nuevo], ids=["legado", "refactor"])
def modulo(request):
    request.param._CACHE.clear()
    return request.param


def test_media_ponderada_por_creditos(modulo):
    expediente = exp(reg("MAT101", "aprobada", 7.0), reg("PRG101", "aprobada", 8.0))
    assert dec(modulo.media(expediente, MAPA)) == Decimal("7.6")


def test_no_documentado_1_convalidada_suma_en_numerador_pero_no_en_denominador(modulo):
    expediente = exp(reg("MAT101", "aprobada", 7.0), reg("FIS101", "convalidada"))
    # (7*6 + 5.0*6) / 6: la convalidada infla la media, que pasa de 10
    assert dec(modulo.media(expediente, MAPA)) == Decimal("12.0")


def test_no_documentado_2_redondeo_por_asignatura_antes_de_acumular(modulo):
    expediente = exp(reg("MAT101", "aprobada", 5.0), reg("PRG101", "aprobada", 5.006))
    # 5.006 se redondea a 5.01 antes de ponderar; con redondeo final daria 5.00
    assert dec(modulo.media(expediente, MAPA)) == Decimal("5.01")


def test_cuenta_el_aprobado_de_mayor_convocatoria_no_la_mejor_nota(modulo):
    expediente = exp(reg("MAT101", "aprobada", 9.0, 1), reg("MAT101", "aprobada", 6.0, 2))
    assert dec(modulo.media(expediente, MAPA)) == Decimal("6.0")


def test_ignora_suspensas_aprobadas_sin_nota_y_asignaturas_fuera_del_plan(modulo):
    expediente = exp(
        reg("MAT101", "suspensa", 3.0),
        reg("XXX999", "aprobada", 10.0),
        reg("ING101", "aprobada", None),
        reg("PRG101", "aprobada", 8.0),
    )
    assert dec(modulo.media(expediente, MAPA)) == Decimal("8.0")


def test_sin_notas_que_cuenten_la_media_es_cero(modulo):
    assert dec(modulo.media(exp(), MAPA)) == 0
    assert dec(modulo.media(exp(reg("FIS101", "convalidada")), MAPA)) == 0


def test_creditos_superados_cuenta_aprobadas_y_convalidadas_una_vez(modulo):
    expediente = exp(
        reg("MAT101", "aprobada", 7.0),
        reg("MAT101", "aprobada", 8.0, 2),
        reg("FIS101", "convalidada"),
        reg("PRG101", "suspensa", 2.0),
    )
    assert modulo.creditos_superados(expediente, MAPA) == 12


def test_progreso_es_porcentaje_sobre_creditos_del_titulo(modulo):
    expediente = exp(reg("MAT101", "aprobada", 7.0), reg("FIS101", "convalidada"))
    assert dec(modulo.progreso(expediente, PLAN, MAPA)) == Decimal("6.25")


def test_convocatorias_no_cuentan_convalidadas_y_limitan_la_matricula(modulo):
    expediente = exp(
        reg("MAT101", "suspensa", 2.0, 1),
        reg("MAT101", "suspensa", 3.0, 2),
        reg("FIS101", "convalidada"),
    )
    assert modulo.convocatorias(expediente) == {"MAT101": 2}
    seis = exp(*[reg("MAT101", "suspensa", 2.0, i) for i in range(1, 7)])
    assert modulo.puede_matricular(seis, "MAT101") is False
    assert modulo.puede_matricular(exp(), "MAT101") is True


def test_calcular_devuelve_el_resumen_y_redondea_en_coma_flotante(modulo):
    resultado = modulo.calcular(exp(reg("MAT101", "aprobada", 7.0), estudiante="EST-1"), RUTA_PLAN)
    # 6*100/192 = 3.125; el round() de float da 3.12, no 3.13
    assert set(resultado) == {"estudiante_id", "nota_media", "creditos_superados", "progreso_pct"}
    assert resultado["estudiante_id"] == "EST-1"
    assert dec(resultado["nota_media"]) == Decimal("7.0")
    assert resultado["creditos_superados"] == 6
    assert dec(resultado["progreso_pct"]) == Decimal("3.12")


def test_calcular_cachea_por_estudiante_y_plan_aunque_cambie_el_expediente(modulo):
    primero = modulo.calcular(exp(reg("MAT101", "aprobada", 7.0), estudiante="EST-2"), RUTA_PLAN)
    segundo = modulo.calcular(exp(reg("MAT101", "aprobada", 9.0), estudiante="EST-2"), RUTA_PLAN)
    assert segundo is primero
    assert dec(segundo["nota_media"]) == Decimal("7.0")
