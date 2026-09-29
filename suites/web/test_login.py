import pytest


@pytest.mark.funcional
@pytest.mark.hu("HU-01")
def test_sin_sesion_redirige_a_login(web_url: str, page) -> None:  # type: ignore[no-untyped-def]
    page.goto(f"{web_url}/inventario")
    assert page.get_by_role("heading", name="Ingresar").is_visible()
