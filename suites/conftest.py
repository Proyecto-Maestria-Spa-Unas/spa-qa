"""Configuración compartida: URLs bajo prueba, credenciales y marcador de trazabilidad a HU."""

import os
from collections.abc import Callable

import httpx
import pytest

API_BASE_URL = os.getenv("API_BASE_URL", "")
WEB_BASE_URL = os.getenv("WEB_BASE_URL", "")

# Roles del plan de pruebas (sección 2). Las credenciales llegan por variables de entorno o secretos de
# GitHub, nunca en el código: QA_<ROL>_CORREO y QA_<ROL>_CONTRASENA. INACTIVO es un usuario desactivado.
ROLES = ("ADMINISTRADOR", "MANICURISTA", "GERENTE")
ROL_INACTIVO = "INACTIVO"

# Las pruebas que crean o cambian datos en el entorno solo corren con QA_PERMITIR_ESCRITURA=1.
PERMITIR_ESCRITURA = os.getenv("QA_PERMITIR_ESCRITURA") == "1"

TIEMPO = 20.0


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


@pytest.fixture(scope="session")
def api(api_url: str) -> str:
    """Prefijo de la versión 1 del contrato."""
    return f"{api_url}/api/v1"


@pytest.fixture(scope="session")
def cliente() -> httpx.Client:
    return httpx.Client(timeout=TIEMPO)


@pytest.fixture(scope="session")
def credenciales() -> Callable[[str], tuple[str, str]]:
    def obtener(rol: str) -> tuple[str, str]:
        correo = os.getenv(f"QA_{rol}_CORREO", "")
        contrasena = os.getenv(f"QA_{rol}_CONTRASENA", "")
        if not correo or not contrasena:
            pytest.skip(f"Faltan QA_{rol}_CORREO o QA_{rol}_CONTRASENA")
        return correo, contrasena

    return obtener


@pytest.fixture(scope="session")
def sesion(
    api: str, cliente: httpx.Client, credenciales: Callable[[str], tuple[str, str]]
) -> Callable[[str], dict]:
    """Cuerpo de POST /auth/login por rol. Inicia sesión una sola vez por rol en toda la corrida."""
    cache: dict[str, dict] = {}

    def obtener(rol: str) -> dict:
        if rol not in cache:
            correo, contrasena = credenciales(rol)
            r = cliente.post(f"{api}/auth/login", json={"correo": correo, "contrasena": contrasena})
            assert r.status_code == 200, f"login de {rol}: {r.status_code} {r.text}"
            cache[rol] = r.json()
        return cache[rol]

    return obtener


@pytest.fixture(scope="session")
def cabeceras(sesion: Callable[[str], dict]) -> Callable[[str], dict[str, str]]:
    def obtener(rol: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {sesion(rol)['access_token']}"}

    return obtener


@pytest.fixture
def escritura() -> None:
    if not PERMITIR_ESCRITURA:
        pytest.skip("Crea o cambia datos en el entorno: requiere QA_PERMITIR_ESCRITURA=1")


def omitir_si_no_implementado(respuesta: httpx.Response, tarea: str) -> None:
    """El andamiaje responde 501 NO_IMPLEMENTADO mientras la tarea no se fusiona: el caso queda omitido."""
    if respuesta.status_code == 501:
        pytest.skip(
            f"{respuesta.request.method} {respuesta.request.url.path} responde 501: pendiente {tarea}"
        )
