"""Equivalencia del refactor del legado sobre el corpus de 500 expedientes.

Compara calculadora_expediente_v1 con calculadora_expediente expediente a
expediente. Solo se admiten las desviaciones declaradas en
src/aula/legado/DESVIACIONES.md; cualquier otra diferencia es un defecto.
"""

from decimal import Decimal

import pytest

from aula.legado import calculadora_expediente as nuevo
from aula.legado import calculadora_expediente_v1 as legado
from herramientas.generar_corpus import generar
from tests.utilidades import RAIZ

RUTA_PLAN = str(RAIZ / "datos" / "planes" / "PLAN-2024.json")
CORPUS = generar()
CENTESIMA = Decimal("0.01")
# Campo -> (desviacion declarada, expedientes del corpus que cambian)
DESVIACIONES = {"nota_media": ("D-01", 29), "progreso_pct": ("D-02", 61)}


@pytest.fixture(scope="module")
def resultados():
    legado._CACHE.clear()
    nuevo._CACHE.clear()
    return [(legado.calcular(e, RUTA_PLAN), nuevo.calcular(e, RUTA_PLAN)) for e in CORPUS]


def test_el_corpus_tiene_500_expedientes():
    assert len(CORPUS) == 500


def test_estudiante_y_creditos_son_identicos(resultados):
    for viejo, refactor in resultados:
        assert refactor["estudiante_id"] == viejo["estudiante_id"]
        assert refactor["creditos_superados"] == viejo["creditos_superados"]


def test_convocatorias_son_identicas():
    for expediente in CORPUS:
        assert nuevo.convocatorias(expediente) == legado.convocatorias(expediente)


@pytest.mark.parametrize("campo", sorted(DESVIACIONES))
def test_solo_cambian_las_desviaciones_declaradas(resultados, campo):
    desviacion, afectados = DESVIACIONES[campo]
    diferencias = [
        (viejo["estudiante_id"], refactor[campo] - Decimal(str(viejo[campo])))
        for viejo, refactor in resultados
        if refactor[campo] != Decimal(str(viejo[campo]))
    ]
    assert all(abs(d) == CENTESIMA for _, d in diferencias), (
        "%s: hay diferencias de mas de una centesima: %s" % (desviacion, diferencias)
    )
    assert len(diferencias) == afectados, "%s declara %d expedientes y cambian %d" % (
        desviacion,
        afectados,
        len(diferencias),
    )
