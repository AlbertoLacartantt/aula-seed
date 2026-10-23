import pytest
from fastapi.testclient import TestClient

from aula import auditoria
from aula.api import app as api
from aula.reglas.motor import VentanaMatricula
from tests.utilidades import expediente, registro

cliente = TestClient(api.app)


@pytest.fixture(autouse=True)
def estado_limpio(tmp_path, monkeypatch):
    """Cada test empieza con la traza temporal y sin expedientes ni matriculas."""
    monkeypatch.setattr(auditoria, "RUTA_TRAZA", tmp_path / "traza.jsonl")
    monkeypatch.setattr(api, "EXPEDIENTES", {})
    monkeypatch.setattr(api, "MATRICULAS", {})


def pedir(codigos, momento="2026-09-10T10:00:00"):
    cuerpo = {"estudiante_id": "EST-0001", "curso_academico": "2026-2027", "codigos": codigos}
    if momento is not None:
        cuerpo["momento"] = momento
    return cliente.post("/matriculas", json=cuerpo)


def test_alta_valida_devuelve_201_y_guarda_la_matricula():
    """La solicitud se evalua con el motor, se responde 201 y queda guardada.

    cubre: SPEC-001/A-14
    """
    r = pedir(["MAT101", "EST101"])
    assert r.status_code == 201
    assert r.json()["version_plan_aplicada"] == "1.2.0"
    assert [l["admitida"] for l in r.json()["lineas"]] == [True, False]
    assert len(api.MATRICULAS["EST-0001"]) == 1


def test_fuera_de_ventana_devuelve_409_y_no_guarda():
    """Ventana cerrada: 409 y nada guardado.

    cubre: SPEC-001/CA-01
    """
    assert pedir(["MAT101"], momento="2026-10-01T00:00:00").status_code == 409
    assert api.MATRICULAS == {}


def test_codigos_duplicados_devuelve_422():
    """Una lista con duplicados es una solicitud invalida.

    cubre: SPEC-001/A-14
    """
    assert pedir(["MAT101", "MAT101"]).status_code == 422


def test_momento_mal_escrito_o_con_zona_horaria_devuelve_422():
    """Un momento que no es ISO-8601 o que trae zona no se puede comparar con la ventana.

    cubre: SPEC-001/A-13
    """
    assert pedir(["MAT101"], momento="10/09/2026").status_code == 422
    assert pedir(["MAT101"], momento="2026-09-10T10:00:00+02:00").status_code == 422


def test_sin_momento_se_usa_la_hora_actual(monkeypatch):
    """Si falta el momento se evalua con la hora del servidor.

    cubre: SPEC-001/A-13
    """
    monkeypatch.setattr(api, "VENTANA",
                        VentanaMatricula("2000-01-01T00:00:00", "2100-01-01T00:00:00"))
    assert pedir(["MAT101"], momento=None).status_code == 201


def test_se_usa_el_expediente_del_estudiante(monkeypatch):
    """Con MAT101 aprobada en su expediente, EST101 se admite.

    cubre: SPEC-001/A-11
    """
    monkeypatch.setattr(api, "EXPEDIENTES",
                        {"EST-0001": expediente(registro("MAT101", "aprobada", 7))})
    assert pedir(["EST101"]).json()["lineas"][0]["admitida"]
