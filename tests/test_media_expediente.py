from decimal import Decimal

from aula.reglas.media import (
    convocatorias_por_asignatura,
    creditos_superados,
    nota_media_ponderada,
    progreso,
)
from tests.utilidades import expediente, plan, registro


def test_media_ponderada_por_creditos_con_dos_decimales():
    """MAT101 (6 cr) con un 7 y PRG101 (9 cr) con un 9: (42 + 81) / 15 = 8,20.

    cubre: SPEC-002/CA-01
    """
    exp = expediente(registro("MAT101", "aprobada", 7), registro("PRG101", "aprobada", 9))
    assert str(nota_media_ponderada(exp, plan())) == "8.20"


def test_punto_medio_redondea_hacia_arriba():
    """Una sola asignatura con 7,005 da 7,01 (half-up), no 7,00.

    cubre: SPEC-002/CA-01
    """
    exp = expediente(registro("MAT101", "aprobada", "7.005"))
    assert nota_media_ponderada(exp, plan()) == Decimal("7.01")


def test_repetida_solo_cuenta_el_aprobado():
    """MAT101 suspensa con un 3 y luego aprobada con un 7; FIS101 con un 9: (42 + 54) / 12 = 8,00.

    cubre: SPEC-002/CA-02
    """
    exp = expediente(
        registro("MAT101", "suspensa", 3, convocatoria=1),
        registro("MAT101", "aprobada", 7, convocatoria=2),
        registro("FIS101", "aprobada", 9),
    )
    assert nota_media_ponderada(exp, plan()) == Decimal("8.00")


def test_convalidada_no_cuenta_en_la_media():
    """PRG101 convalidada no entra aunque traiga nota: (42 + 54) / 12 = 8,00.

    cubre: SPEC-002/CA-03
    """
    exp = expediente(
        registro("PRG101", "convalidada", 10),
        registro("MAT101", "aprobada", 7),
        registro("FIS101", "aprobada", 9),
    )
    assert nota_media_ponderada(exp, plan()) == Decimal("8.00")


def test_redondeo_una_sola_vez_al_final():
    """(6,665 + 7,004) / 2 = 6,8345 -> 6,83. Redondeando cada nota antes saldria 6,84.

    cubre: SPEC-002/CA-04, SPEC-002/INV-01
    """
    exp = expediente(
        registro("MAT101", "aprobada", "6.665"), registro("FIS101", "aprobada", "7.004")
    )
    assert nota_media_ponderada(exp, plan()) == Decimal("6.83")


def test_convalidada_cuenta_como_superada():
    """PRG101 convalidada (9 cr) y MAT101 aprobada (6 cr): 15 creditos.

    cubre: SPEC-002/CA-05
    """
    exp = expediente(registro("PRG101", "convalidada"), registro("MAT101", "aprobada", 7))
    assert creditos_superados(exp, plan()) == 15


def test_progreso_en_porcentaje_con_dos_decimales():
    """6 de 192 creditos: 3,125 % -> 3,13.

    cubre: SPEC-002/CA-06
    """
    exp = expediente(registro("MAT101", "aprobada", 7))
    assert progreso(exp, plan()) == Decimal("3.13")


def test_sin_asignaturas_que_cuenten_da_cero():
    """Solo un suspenso y una convalidada: 0,00. Expediente vacio: todo a cero.

    cubre: SPEC-002/CA-07
    """
    exp = expediente(registro("MAT101", "suspensa", 4), registro("PRG101", "convalidada"))
    assert str(nota_media_ponderada(exp, plan())) == "0.00"
    vacio = expediente()
    assert str(nota_media_ponderada(vacio, plan())) == "0.00"
    assert creditos_superados(vacio, plan()) == 0
    assert str(progreso(vacio, plan())) == "0.00"


def test_resultados_en_decimal():
    """La media y el progreso son Decimal, nunca float.

    cubre: SPEC-002/INV-02
    """
    exp = expediente(registro("MAT101", "aprobada", 7))
    assert isinstance(nota_media_ponderada(exp, plan()), Decimal)
    assert isinstance(progreso(exp, plan()), Decimal)


def test_mismo_resultado_sin_importar_el_orden():
    """MAT101 aprobada en convocatoria 2 (9) y en la 4 (6): cuenta el 6 de la ultima, en cualquier orden.

    cubre: SPEC-002/INV-03
    """
    conv2 = registro("MAT101", "aprobada", 9, convocatoria=2)
    conv4 = registro("MAT101", "aprobada", 6, convocatoria=4)
    assert nota_media_ponderada(expediente(conv2, conv4), plan()) == Decimal("6.00")
    assert nota_media_ponderada(expediente(conv4, conv2), plan()) == Decimal("6.00")


def test_convocatorias_por_asignatura_sin_contar_convalidaciones():
    """MAT101 suspensa y luego aprobada: 2. PRG101 convalidada: 0. FIS101 sin registros: no sale.

    cubre: SPEC-002/CA-09
    """
    exp = expediente(
        registro("MAT101", "suspensa", 3, convocatoria=1),
        registro("MAT101", "aprobada", 7, convocatoria=2),
        registro("PRG101", "convalidada"),
    )
    assert convocatorias_por_asignatura(exp, plan()) == {"MAT101": 2, "PRG101": 0}
