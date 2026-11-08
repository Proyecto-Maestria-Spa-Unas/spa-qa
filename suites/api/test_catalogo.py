"""Q2 · Catálogo (HU-02, HU-03/04, HU-05) contra staging. Casos de docs/PLAN_PRUEBAS.md §3.

Los endpoints que aún responden 501 dejan sus casos omitidos con la tarea pendiente (B4 o B9); cuando la
tarea se fusiona y se despliega, los mismos casos empiezan a correr sin cambiar este archivo.
Los productos que crean estas pruebas llevan el prefijo QA- y quedan descontinuados al final (no hay borrado).
"""

import uuid
from collections.abc import Callable, Iterator

import httpx
import pytest

from suites.conftest import omitir_si_no_implementado

ID_INEXISTENTE = "00000000-0000-4000-8000-000000000000"


def _productos(cliente: httpx.Client, api: str, cabeceras: dict[str, str], **params: str | int) -> dict:
    r = cliente.get(f"{api}/productos", headers=cabeceras, params=params)
    assert r.status_code == 200, r.text
    return r.json()


# ── HU-03 / HU-04 · Consultar inventario y filtrar ──────────────────────────
@pytest.mark.funcional
@pytest.mark.hu("HU-03")
def test_cp_hu03_01_lista_sin_descontinuados(
    api: str, cliente: httpx.Client, cabeceras: Callable[[str], dict[str, str]]
) -> None:
    cuerpo = _productos(cliente, api, cabeceras("MANICURISTA"))
    assert set(cuerpo) >= {"items", "total", "page", "size"}
    assert all(not p["descontinuado"] and p["estado"] != "DESCONTINUADO" for p in cuerpo["items"])


@pytest.mark.funcional
@pytest.mark.hu("HU-03")
def test_cp_hu03_02_incluir_descontinuados(
    api: str, cliente: httpx.Client, cabeceras: Callable[[str], dict[str, str]]
) -> None:
    h = cabeceras("MANICURISTA")
    sin = _productos(cliente, api, h)["total"]
    con = _productos(cliente, api, h, incluir_descontinuados="true")["total"]
    assert con >= sin


@pytest.mark.funcional
@pytest.mark.hu("HU-03")
@pytest.mark.parametrize("estado", ["AGOTADO", "BAJO_STOCK", "DISPONIBLE"])
def test_cp_hu03_04_filtro_por_estado(
    estado: str, api: str, cliente: httpx.Client, cabeceras: Callable[[str], dict[str, str]]
) -> None:
    items = _productos(cliente, api, cabeceras("MANICURISTA"), estado=estado, size=100)["items"]
    assert all(p["estado"] == estado for p in items)


@pytest.mark.funcional
@pytest.mark.hu("HU-03")
def test_cp_hu03_05_paginacion(
    api: str, cliente: httpx.Client, cabeceras: Callable[[str], dict[str, str]]
) -> None:
    h = cabeceras("MANICURISTA")
    primera = _productos(cliente, api, h, page=1, size=1)
    if primera["total"] < 2:
        pytest.skip("se necesitan al menos 2 productos en el entorno (datos de D11)")
    segunda = _productos(cliente, api, h, page=2, size=1)
    assert primera["total"] == segunda["total"]
    assert primera["items"][0]["id"] != segunda["items"][0]["id"]


@pytest.mark.funcional
@pytest.mark.hu("HU-03")
def test_cp_hu03_07_producto_inexistente(
    api: str, cliente: httpx.Client, cabeceras: Callable[[str], dict[str, str]]
) -> None:
    r = cliente.get(f"{api}/productos/{ID_INEXISTENTE}", headers=cabeceras("MANICURISTA"))
    assert r.status_code == 404, r.text
    assert r.json()["code"] == "RECURSO_NO_EXISTE"


@pytest.mark.funcional
@pytest.mark.hu("HU-04")
def test_cp_hu04_01_solo_categorias_activas(
    api: str, cliente: httpx.Client, cabeceras: Callable[[str], dict[str, str]]
) -> None:
    r = cliente.get(f"{api}/categorias", headers=cabeceras("MANICURISTA"))
    omitir_si_no_implementado(r, "B4")
    assert r.status_code == 200, r.text
    assert r.json(), "staging tiene 8 categorías de referencia"
    assert all(c["activa"] for c in r.json())


@pytest.mark.funcional
@pytest.mark.hu("HU-04")
def test_cp_hu04_02_filtro_por_categoria(
    api: str, cliente: httpx.Client, cabeceras: Callable[[str], dict[str, str]]
) -> None:
    h = cabeceras("MANICURISTA")
    r = cliente.get(f"{api}/categorias", headers=h)
    omitir_si_no_implementado(r, "B4")
    categoria = r.json()[0]["id"]
    items = _productos(cliente, api, h, categoria_id=categoria, size=100)["items"]
    assert all(p["categoria_id"] == categoria for p in items)


# ── HU-02 / HU-05 · Registrar y editar producto ─────────────────────────────
@pytest.mark.funcional
@pytest.mark.hu("HU-02")
def test_cp_hu02_01_unidades_de_medida(
    api: str, cliente: httpx.Client, cabeceras: Callable[[str], dict[str, str]]
) -> None:
    r = cliente.get(f"{api}/unidades-medida", headers=cabeceras("MANICURISTA"))
    omitir_si_no_implementado(r, "B4")
    assert r.status_code == 200, r.text
    assert len(r.json()) == 12
    assert all(isinstance(u["admite_decimales"], bool) for u in r.json())


@pytest.fixture
def producto_qa(
    escritura: None, api: str, cliente: httpx.Client, cabeceras: Callable[[str], dict[str, str]]
) -> Iterator[dict]:
    """Producto QA-… creado por el administrador; al terminar se descontinúa (RN-12: no hay borrado)."""
    h = cabeceras("ADMINISTRADOR")
    categorias = cliente.get(f"{api}/categorias", headers=h)
    omitir_si_no_implementado(categorias, "B4")
    unidades = cliente.get(f"{api}/unidades-medida", headers=h)
    omitir_si_no_implementado(unidades, "B4")
    unidad = next(u for u in unidades.json() if not u["admite_decimales"])
    creado = cliente.post(
        f"{api}/productos",
        headers=h,
        json={
            "codigo": f"QA-{uuid.uuid4().hex[:8].upper()}",
            "nombre": "Producto de prueba QA",
            "categoria_id": categorias.json()[0]["id"],
            "unidad_medida_id": unidad["id"],
        },
    )
    omitir_si_no_implementado(creado, "B9")
    assert creado.status_code == 201, creado.text
    yield creado.json()
    cliente.post(f"{api}/productos/{creado.json()['id']}/descontinuar", headers=h)


@pytest.mark.funcional
@pytest.mark.hu("HU-02")
def test_cp_hu02_02_producto_nuevo_sin_stock(producto_qa: dict) -> None:
    assert float(producto_qa["stock_actual"]) == 0
    assert producto_qa["estado"] == "AGOTADO"


@pytest.mark.funcional
@pytest.mark.hu("HU-02")
def test_cp_hu02_04_codigo_duplicado_sin_importar_mayusculas(
    producto_qa: dict, api: str, cliente: httpx.Client, cabeceras: Callable[[str], dict[str, str]]
) -> None:
    r = cliente.post(
        f"{api}/productos",
        headers=cabeceras("ADMINISTRADOR"),
        json={
            "codigo": producto_qa["codigo"].lower(),
            "nombre": "Duplicado QA",
            "categoria_id": producto_qa["categoria_id"],
            "unidad_medida_id": producto_qa["unidad_medida_id"],
        },
    )
    assert r.status_code == 409, r.text
    assert r.json()["code"] == "CODIGO_DUPLICADO"


@pytest.mark.funcional
@pytest.mark.hu("HU-05")
def test_cp_hu05_01_y_02_bloqueo_optimista(
    producto_qa: dict, api: str, cliente: httpx.Client, cabeceras: Callable[[str], dict[str, str]]
) -> None:
    h = cabeceras("ADMINISTRADOR")
    url, version = f"{api}/productos/{producto_qa['id']}", producto_qa["version"]

    ok = cliente.patch(
        url, headers={**h, "If-Match": str(version)}, json={"nombre": "Producto de prueba QA editado"}
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["version"] == version + 1

    viejo = cliente.patch(url, headers={**h, "If-Match": str(version)}, json={"nombre": "Otro nombre QA"})
    assert viejo.status_code == 412, viejo.text
    assert viejo.json()["code"] == "VERSION_CONFLICTO"
