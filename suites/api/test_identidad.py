"""Q2 · HU-01 (iniciar sesión) y HU-09 (gestionar usuarios) contra staging. Casos de PLAN_PRUEBAS.md §3."""

import uuid
from collections.abc import Callable

import httpx
import pytest

from suites.conftest import ROL_INACTIVO, ROLES

CLAVE_TEMPORAL = "Temporal-QA-2026"


def _correo_nuevo() -> str:
    return f"qa-{uuid.uuid4().hex[:10]}@example.test"


# ── HU-01 · Iniciar sesión ──────────────────────────────────────────────────
@pytest.mark.funcional
@pytest.mark.hu("HU-01")
@pytest.mark.parametrize("rol", ROLES)
def test_cp_hu01_01_login_valido(rol: str, sesion: Callable[[str], dict]) -> None:
    cuerpo = sesion(rol)
    assert cuerpo["access_token"]
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["expires_in"] > 0
    assert cuerpo["usuario"]["rol"] == rol
    assert cuerpo["usuario"]["permisos"], "el usuario debe traer sus permisos"


@pytest.mark.funcional
@pytest.mark.hu("HU-01")
def test_cp_hu01_02_y_03_no_revela_cuentas(
    api: str, cliente: httpx.Client, credenciales: Callable[[str], tuple[str, str]]
) -> None:
    correo, _ = credenciales("ADMINISTRADOR")
    mala = cliente.post(f"{api}/auth/login", json={"correo": correo, "contrasena": "Incorrecta-QA-1"})
    inexistente = cliente.post(
        f"{api}/auth/login", json={"correo": _correo_nuevo(), "contrasena": "Incorrecta-QA-1"}
    )
    for r in (mala, inexistente):
        assert r.status_code == 401, r.text
        assert r.json()["code"] == "CREDENCIALES_INVALIDAS"
    # Mismo mensaje en los dos casos: la respuesta no permite saber si la cuenta existe.
    assert mala.json()["detail"] == inexistente.json()["detail"]


@pytest.mark.funcional
@pytest.mark.hu("HU-01")
def test_cp_hu01_04_usuario_inactivo(
    api: str, cliente: httpx.Client, credenciales: Callable[[str], tuple[str, str]]
) -> None:
    correo, contrasena = credenciales(ROL_INACTIVO)
    r = cliente.post(f"{api}/auth/login", json={"correo": correo, "contrasena": contrasena})
    assert r.status_code == 403, r.text
    assert r.json()["code"] == "USUARIO_INACTIVO"


@pytest.mark.funcional
@pytest.mark.hu("HU-01")
@pytest.mark.parametrize(
    "cuerpo",
    [{"contrasena": "Suficiente-123"}, {"correo": "alguien@spa.co", "contrasena": "corta"}],
    ids=["sin-correo", "contrasena-corta"],
)
def test_cp_hu01_05_datos_invalidos(api: str, cliente: httpx.Client, cuerpo: dict) -> None:
    r = cliente.post(f"{api}/auth/login", json=cuerpo)
    assert r.status_code == 422, r.text
    assert r.json()["code"] == "DATOS_INVALIDOS"


@pytest.mark.funcional
@pytest.mark.hu("HU-01")
@pytest.mark.parametrize("rol", ROLES)
def test_cp_hu01_06_me_coincide_con_el_login(
    rol: str, api: str, cliente: httpx.Client, sesion: Callable[[str], dict], cabeceras: Callable[[str], dict]
) -> None:
    r = cliente.get(f"{api}/auth/me", headers=cabeceras(rol))
    assert r.status_code == 200, r.text
    yo, login = r.json(), sesion(rol)["usuario"]
    assert (yo["id"], yo["correo"], yo["rol"]) == (login["id"], login["correo"], login["rol"])
    assert sorted(yo["permisos"]) == sorted(login["permisos"])


@pytest.mark.funcional
@pytest.mark.hu("HU-01")
def test_cp_hu01_07_me_sin_token_o_alterado(
    api: str, cliente: httpx.Client, sesion: Callable[[str], dict]
) -> None:
    token = sesion("MANICURISTA")["access_token"]
    alterado = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
    for cabecera in ({}, {"Authorization": f"Bearer {alterado}"}, {"Authorization": "Bearer no-es-un-jwt"}):
        r = cliente.get(f"{api}/auth/me", headers=cabecera)
        assert r.status_code == 401, (cabecera, r.text)
        assert r.json()["code"] == "NO_AUTENTICADO"


# ── HU-09 · Gestionar usuarios ──────────────────────────────────────────────
@pytest.mark.funcional
@pytest.mark.hu("HU-09")
def test_cp_hu09_02_correo_ya_registrado(
    api: str,
    cliente: httpx.Client,
    cabeceras: Callable[[str], dict],
    credenciales: Callable[[str], tuple[str, str]],
) -> None:
    correo, _ = credenciales("MANICURISTA")
    r = cliente.post(
        f"{api}/usuarios",
        headers=cabeceras("ADMINISTRADOR"),
        json={
            "correo": correo,
            "nombre_completo": "Duplicado QA",
            "rol": "MANICURISTA",
            "contrasena_temporal": CLAVE_TEMPORAL,
        },
    )
    assert r.status_code == 409, r.text


@pytest.mark.funcional
@pytest.mark.hu("HU-09")
@pytest.mark.parametrize(
    ("filtro", "campo", "valor"), [("activo", "activo", True), ("rol", "rol", "MANICURISTA")]
)
def test_cp_hu09_03_filtros(
    filtro: str, campo: str, valor: object, api: str, cliente: httpx.Client, cabeceras: Callable[[str], dict]
) -> None:
    parametro = str(valor).lower() if isinstance(valor, bool) else str(valor)
    r = cliente.get(
        f"{api}/usuarios", headers=cabeceras("ADMINISTRADOR"), params={filtro: parametro, "size": 100}
    )
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert items, f"se esperaba al menos un usuario con {filtro}={valor}"
    assert all(u[campo] == valor for u in items)


@pytest.mark.funcional
@pytest.mark.hu("HU-09")
def test_cp_hu09_06_no_existe_borrado(
    api: str, cliente: httpx.Client, cabeceras: Callable[[str], dict], sesion: Callable[[str], dict]
) -> None:
    r = cliente.delete(
        f"{api}/usuarios/{sesion('MANICURISTA')['usuario']['id']}", headers=cabeceras("ADMINISTRADOR")
    )
    assert r.status_code == 405, r.text


@pytest.mark.funcional
@pytest.mark.hu("HU-09")
def test_cp_hu09_07_roles_y_permisos(
    api: str, cliente: httpx.Client, cabeceras: Callable[[str], dict], sesion: Callable[[str], dict]
) -> None:
    r = cliente.get(f"{api}/roles", headers=cabeceras("ADMINISTRADOR"))
    assert r.status_code == 200, r.text
    roles = {rol["codigo"]: sorted(rol["permisos"]) for rol in r.json()}
    assert set(roles) == set(ROLES)
    # Los permisos que entrega el login de cada rol son los mismos que publica /roles.
    for rol in ROLES:
        assert sorted(sesion(rol)["usuario"]["permisos"]) == roles[rol], rol
    # Sección 4: la manicurista no gestiona usuarios ni consulta analítica, pero sí registra salidas.
    assert "usuario.gestionar" not in roles["MANICURISTA"]
    assert "analitica.consultar" not in roles["MANICURISTA"]
    assert "movimiento.registrar_salida" in roles["MANICURISTA"]


@pytest.mark.funcional
@pytest.mark.hu("HU-09")
@pytest.mark.usefixtures("escritura")
def test_cp_hu09_01_04_05_alta_cambio_y_desactivacion(
    api: str, cliente: httpx.Client, cabeceras: Callable[[str], dict]
) -> None:
    """Crea qa-…@example.test (no hay borrado: queda desactivado al final)."""
    admin = cabeceras("ADMINISTRADOR")
    correo = _correo_nuevo()
    creado = cliente.post(
        f"{api}/usuarios",
        headers=admin,
        json={
            "correo": correo,
            "nombre_completo": "Usuario QA",
            "rol": "MANICURISTA",
            "contrasena_temporal": CLAVE_TEMPORAL,
        },
    )
    assert creado.status_code == 201, creado.text
    usuario_id = creado.json()["id"]

    def login() -> httpx.Response:
        return cliente.post(f"{api}/auth/login", json={"correo": correo, "contrasena": CLAVE_TEMPORAL})

    # CP-HU09-01: puede iniciar sesión.
    primera = login()
    assert primera.status_code == 200, primera.text
    assert primera.json()["usuario"]["rol"] == "MANICURISTA"

    # CP-HU09-04: el nuevo rol aplica en el siguiente login.
    cambio = cliente.patch(f"{api}/usuarios/{usuario_id}", headers=admin, json={"rol": "GERENTE"})
    assert cambio.status_code == 200, cambio.text
    assert login().json()["usuario"]["rol"] == "GERENTE"

    # CP-HU09-05: desactivado recibe 403 USUARIO_INACTIVO.
    estado = cliente.patch(f"{api}/usuarios/{usuario_id}/estado", headers=admin, json={"activo": False})
    assert estado.status_code == 200, estado.text
    final = login()
    assert final.status_code == 403, final.text
    assert final.json()["code"] == "USUARIO_INACTIVO"
