"""Configuración compartida: URLs de los componentes bajo prueba y marcador de trazabilidad a HU."""

import os

import pytest

API_BASE_URL = os.getenv("API_BASE_URL", "")
WEB_BASE_URL = os.getenv("WEB_BASE_URL", "")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Toda prueba funcional debe declarar la historia de usuario que valida."""
    for item in items:
        if "funcional" in item.keywords and item.get_closest_marker("hu") is None:
            raise pytest.UsageError(f"{item.nodeid}: prueba funcional sin @pytest.mark.hu('HU-xx')")


@pytest.fixture(scope="session")
def api_url() -> str:
    if not API_BASE_URL:
        pytest.skip("API_BASE_URL no definida")
    return API_BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def web_url() -> str:
    if not WEB_BASE_URL:
        pytest.skip("WEB_BASE_URL no definida")
    return WEB_BASE_URL.rstrip("/")
