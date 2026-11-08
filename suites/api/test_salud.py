import httpx
import pytest


@pytest.mark.humo
def test_api_responde_salud(api_url: str) -> None:
    respuesta = httpx.get(f"{api_url}/api/v1/health", timeout=10)
    assert respuesta.status_code == 200
    assert respuesta.json()["status"] == "ok"
