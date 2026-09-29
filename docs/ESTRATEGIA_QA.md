# Estrategia de QA

| Nivel | Dónde vive | Cuándo corre | Responsable |
|---|---|---|---|
| Unitarias | Cada repo (`tests/`, `*.test.jsx`) | Cada PR (`calidad / pipeline`) | Desarrolladores |
| SQL / reglas de stock | `spa-database/tests/sql` | Cada PR | equipo-datos |
| API funcional y contrato | `spa-qa/suites/api` | PR de backend (`qa-gate / qa`) | equipo-qa |
| E2E navegador | `spa-qa/suites/web` (Playwright) | PR de frontend (`qa-gate / qa`) | equipo-qa |
| Carga | `spa-qa/suites/carga` (k6) | Programado contra staging | equipo-qa + devops |

**Trazabilidad:** toda prueba marcada `@pytest.mark.funcional` debe declarar `@pytest.mark.hu("HU-xx")`;
la colección falla si falta. Reporte por HU: `pytest -m "hu" --collect-only -q`.

**Activación de la puerta:** ver `spa-devops-workflows/README.md` (secreto `QA_READ_TOKEN` + `ENABLE_QA_GATE=true`).
