"""Q2 · Matriz de permisos de docs/PLAN_PRUEBAS.md §4 convertida en casos 401/403.

PASA = el rol supera el control de permiso: la respuesta no es 401 ni 403 (puede ser 200, 404, 422 o 501).
Las peticiones de escritura van con cuerpo vacío o con un id que no existe: el control de permiso se evalúa
antes de validar el cuerpo, así que estas pruebas no crean ni cambian datos.
"""

from collections.abc import Callable

import httpx
import pytest

from suites.conftest import ROLES

PASA, PROHIBIDO = "PASA", 403
ID = "00000000-0000-4000-8000-000000000000"

# (ID, método, ruta, ADMINISTRADOR, MANICURISTA, GERENTE). PM-23 y PM-24 son públicos y no están aquí.
MATRIZ = [
    ("PM-01", "GET", "/alertas", PASA, PASA, PASA),
    ("PM-02", "GET", "/alertas/resumen", PASA, PASA, PASA),
    ("PM-03", "GET", "/analitica/tablero", PASA, PROHIBIDO, PASA),
    ("PM-04", "GET", "/analitica/consumo", PASA, PROHIBIDO, PASA),
    ("PM-05", "GET", "/analitica/cobertura", PASA, PROHIBIDO, PASA),
    ("PM-06", "GET", "/analitica/exportar", PASA, PROHIBIDO, PASA),
    ("PM-07", "GET", "/analitica/kardex", PASA, PROHIBIDO, PASA),
    ("PM-08", "GET", "/analitica/proveedores-cercanos", PASA, PASA, PASA),
    ("PM-09", "GET", "/categorias", PASA, PASA, PASA),
    ("PM-10", "POST", "/categorias", PASA, PROHIBIDO, PROHIBIDO),
    ("PM-11", "PATCH", "/categorias/999999", PASA, PROHIBIDO, PROHIBIDO),
    ("PM-12", "GET", "/unidades-medida", PASA, PASA, PASA),
    ("PM-13", "GET", "/productos", PASA, PASA, PASA),
    ("PM-14", "POST", "/productos", PASA, PROHIBIDO, PROHIBIDO),
    ("PM-15", "GET", f"/productos/{ID}", PASA, PASA, PASA),
    ("PM-16", "PATCH", f"/productos/{ID}", PASA, PROHIBIDO, PROHIBIDO),
    ("PM-17", "PUT", f"/productos/{ID}/stock-minimo", PASA, PROHIBIDO, PROHIBIDO),
    ("PM-18", "POST", f"/productos/{ID}/descontinuar", PASA, PROHIBIDO, PROHIBIDO),
    ("PM-19", "POST", f"/productos/{ID}/reactivar", PASA, PROHIBIDO, PROHIBIDO),
    ("PM-20", "GET", "/proveedores", PASA, PASA, PASA),
    ("PM-21", "POST", "/proveedores", PASA, PROHIBIDO, PROHIBIDO),
    ("PM-22", "PATCH", f"/proveedores/{ID}", PASA, PROHIBIDO, PROHIBIDO),
    ("PM-25", "GET", "/auth/me", PASA, PASA, PASA),
    ("PM-26", "GET", "/usuarios", PASA, PROHIBIDO, PASA),
    ("PM-27", "POST", "/usuarios", PASA, PROHIBIDO, PASA),
    ("PM-28", "GET", f"/usuarios/{ID}", PASA, PROHIBIDO, PASA),
    ("PM-29", "PATCH", f"/usuarios/{ID}", PASA, PROHIBIDO, PASA),
    ("PM-30", "PATCH", f"/usuarios/{ID}/estado", PASA, PROHIBIDO, PASA),
    ("PM-31", "GET", "/roles", PASA, PROHIBIDO, PASA),
    ("PM-32", "GET", "/motivos-movimiento", PASA, PASA, PASA),
    ("PM-33", "POST", "/movimientos/entradas", PASA, PROHIBIDO, PROHIBIDO),
    ("PM-34", "POST", "/movimientos/salidas", PASA, PASA, PROHIBIDO),
    ("PM-35", "GET", "/movimientos", PASA, PASA, PASA),
    ("PM-36", "GET", f"/movimientos/{ID}", PASA, PASA, PASA),
    ("PM-37", "POST", f"/movimientos/{ID}/anulaciones", PASA, PROHIBIDO, PROHIBIDO),
]

CASOS_ROL = [
    pytest.param(metodo, ruta, rol, esperado, id=f"{caso}-{rol}")
    for caso, metodo, ruta, *por_rol in MATRIZ
    for rol, esperado in zip(ROLES, por_rol, strict=True)
]


def _pedir(
    cliente: httpx.Client, api: str, metodo: str, ruta: str, cabeceras: dict[str, str]
) -> httpx.Response:
    cuerpo: dict[str, object] | None = {} if metodo in ("POST", "PUT", "PATCH") else None
    return cliente.request(metodo, f"{api}{ruta}", headers=cabeceras, json=cuerpo)


@pytest.mark.parametrize(("metodo", "ruta"), [pytest.param(m, r, id=c) for c, m, r, *_ in MATRIZ])
def test_sin_token_es_401(api: str, cliente: httpx.Client, metodo: str, ruta: str) -> None:
    r = _pedir(cliente, api, metodo, ruta, {})
    assert r.status_code == 401, r.text
    assert r.json()["code"] == "NO_AUTENTICADO"


@pytest.mark.parametrize(("metodo", "ruta", "rol", "esperado"), CASOS_ROL)
def test_permiso_por_rol(
    api: str,
    cliente: httpx.Client,
    cabeceras: Callable[[str], dict[str, str]],
    metodo: str,
    ruta: str,
    rol: str,
    esperado: object,
) -> None:
    r = _pedir(cliente, api, metodo, ruta, cabeceras(rol))
    if esperado == PROHIBIDO:
        assert r.status_code == 403, r.text
        assert r.json()["code"] == "SIN_PERMISO"
    else:
        assert r.status_code not in (401, 403), r.text
