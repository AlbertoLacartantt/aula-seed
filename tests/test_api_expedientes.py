from fastapi.testclient import TestClient

from aula.api import app as api
from tests.utilidades import expediente, registro

cliente = TestClient(api.app)


def test_consulta_de_expediente(monkeypatch):
    """Con expediente devuelve el resumen con dos decimales; sin expediente, 404.

    cubre: SPEC-002/CA-08
    """
    exp = expediente(registro("MAT101", "aprobada", 7), registro("PRG101", "aprobada", 9))
    monkeypatch.setattr(api, "EXPEDIENTES", {"EST-0001": exp})
    r = cliente.get("/expedientes/EST-0001")
    assert r.status_code == 200
    assert r.json()["nota_media"] == "8.20"
    assert r.json()["creditos_superados"] == 15
    assert r.json()["progreso"] == "7.81"
    assert cliente.get("/expedientes/EST-9999").status_code == 404
