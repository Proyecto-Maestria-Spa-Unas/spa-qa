import httpx
import pytest


@pytest.mark.humo
def test_api_responde_salud(api_url: str) -> None:
    respuesta = httpx.get(f"{api_url}/api/v1/health", timeout=10)
    assert respuesta.status_code == 200
    assert respuesta.json()["status"] == "ok"


@pytest.mark.funcional
@pytest.mark.hu("HU-01")
@pytest.mark.skip(reason="Pendiente: endpoint /api/v1/auth/login")
def test_credenciales_invalidas_no_permiten_acceso(api_url: str) -> None:
    respuesta = httpx.post(f"{api_url}/api/v1/auth/login", json={"usuario": "x", "clave": "mala"}, timeout=10)
    assert respuesta.status_code == 401
