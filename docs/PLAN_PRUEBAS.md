# Plan de pruebas · Entregas 1 y 2

| | |
|---|---|
| **Tarea** | Q1 · spa-qa#1 |
| **Responsable** | @jhonjairosolerumbarila-ops (QA) |
| **Versión** | 1.0 · 31-oct-2026 |
| **Alcance** | 37 endpoints de `/api/v1` (4 servicios), pantallas de las Entregas 1 y 2 y reglas de la base |

## 0. Fuentes verificadas

Este plan no contiene datos de memoria. Cada tabla sale de una de estas fuentes, verificadas el 31-oct-2026:

| Dato | Fuente |
|---|---|
| Endpoints, permiso exigido y trazabilidad HU/RF/RN | `spa-backend-api/docs/openapi/*-v1.yaml`, rama `develop`, commit `fb3c464` |
| Códigos de error y estados HTTP | `spa-backend-api/app/compartido/errores.py`, commit `fb3c464` |
| Permisos por rol | Documento de arquitectura, sección 6 «Matriz de permisos por rol», revisión 15 |
| Tareas, entregas y criterios de aceptación | Issues `plan-entregas` (campos Entrega, Depende de, Criterios) |
| Reglas de estado e inventario en la base | `spa-database/tests/sql/0002` y `0003` (fusionadas en #24 y #25) |

Si una fuente cambia (por ejemplo, el grupo decide DEC-01..04 en A1), este plan se actualiza en un PR y se indica la nueva versión.

## 1. Niveles de prueba

Se mantiene la estrategia de `docs/ESTRATEGIA_QA.md`. Este plan define **qué** se prueba en cada nivel y **cuándo** se considera aprobada cada entrega.

| Nivel | Dónde | Tarea | Entrega |
|---|---|---|---|
| Contrato y seguridad (37 endpoints) | `spa-backend-api/tests/contrato/` (ya existe, corre en cada PR) | B2 · cerrada | 1 y 2 |
| Reglas SQL del catálogo | `spa-database/tests/sql/` (corre en cada PR) | D4 · cerrada | 1 |
| API funcional contra staging | `spa-qa/suites/api/` | Q2 (Entrega 1) · Q4 (Entrega 2) | 1 y 2 |
| E2E en navegador | `spa-qa/suites/web/` (Playwright) | Q3 | 2 |
| Carga | `spa-qa/suites/carga/` | Q5 | 2 |

Convención obligatoria (ya la exige `suites/conftest.py`): toda prueba `@pytest.mark.funcional` declara `@pytest.mark.hu("HU-xx")`. Las pruebas de permisos usan además el identificador `PM-xx` de la sección 4 en su nombre.

## 2. Entornos y datos

| Entorno | URL | Uso |
|---|---|---|
| Staging API | Alias de Vercel de la rama `develop` (`API_BASE_URL`) | Q2, Q4, Q5 |
| Staging web | Preview de Vercel del frontend (`WEB_BASE_URL`) | Q3 |
| Base staging | Supabase staging (cambios solo por pipeline `cd`) | Datos de referencia: 8 categorías y 12 unidades (verificado 31-oct) |

**Usuarios de prueba (precondición):** un usuario activo por rol (Administrador, Manicurista, Gerente) y un usuario inactivo. Se crean cuando existan D5 (roles y permisos en la base) y B5/B6 (Supabase Auth). Sus credenciales se guardan como secretos del entorno, nunca en el repositorio.

**Datos de movimientos y analítica:** D11 (datos de demostración). Las pruebas de la Entrega 2 que dependen de saldos o costos crean sus propios datos y los identifican con el prefijo `QA-`.

## 3. Casos por historia de usuario

Formato: **ID · condición · resultado esperado**. El nombre de cada HU se toma de la funcionalidad del endpoint en el contrato; el texto oficial de cada historia está en el documento de requisitos. El código entre comillas es el `code` del cuerpo `application/problem+json`. «Endpoint» y «Traza» se copian del contrato.

### Entrega 1 (cierra con R1)

**HU-01 · Iniciar sesión** · `POST /auth/login`, `GET /auth/me` · tareas B5, F6

| ID | Condición | Esperado |
|---|---|---|
| CP-HU01-01 | Correo y contraseña válidos de un usuario activo | 200 con `access_token`, `expires_in`, rol y permisos |
| CP-HU01-02 | Contraseña incorrecta | 401 `CREDENCIALES_INVALIDAS` |
| CP-HU01-03 | Correo no registrado | 401 `CREDENCIALES_INVALIDAS` (mismo mensaje que 01-02: no revela cuentas) |
| CP-HU01-04 | Usuario desactivado con contraseña correcta | 403 `USUARIO_INACTIVO` |
| CP-HU01-05 | Cuerpo sin `correo` o contraseña de menos de 8 caracteres | 422 `DATOS_INVALIDOS` |
| CP-HU01-06 | `GET /auth/me` con token válido | 200 con perfil, rol y permisos que coinciden con la sección 4 |
| CP-HU01-07 | `GET /auth/me` sin token, con token alterado o vencido | 401 `NO_AUTENTICADO` |
| CP-HU01-08 | Pantalla: el menú solo muestra opciones con permiso (RNF-07) | Manicurista no ve Usuarios ni Analítica |

**HU-09 · Gestionar usuarios** · `/usuarios`, `/roles` · tareas B6, F8

| ID | Condición | Esperado |
|---|---|---|
| CP-HU09-01 | Crear usuario con correo, nombre, rol y contraseña temporal | 201; el usuario puede iniciar sesión |
| CP-HU09-02 | Crear usuario con un correo ya registrado | 409 |
| CP-HU09-03 | Listar con filtros `activo` y `rol` | Solo los que cumplen el filtro |
| CP-HU09-04 | Cambiar nombre o rol | 200; el nuevo rol aplica en el siguiente login |
| CP-HU09-05 | Desactivar (`PATCH /usuarios/{id}/estado` con `activo: false`) | 200; ese usuario recibe 403 `USUARIO_INACTIVO` al iniciar sesión |
| CP-HU09-06 | `DELETE /usuarios/{id}` | 405 (no existe borrado) |
| CP-HU09-07 | `GET /roles` | Los 3 roles con los permisos de la sección 4 |

**HU-02 · Registrar producto** · `POST /productos`, `GET /unidades-medida` · tareas B4, B9, F11

| ID | Condición | Esperado |
|---|---|---|
| CP-HU02-01 | `GET /unidades-medida` | 12 unidades con `admite_decimales` |
| CP-HU02-02 | Crear producto válido sin `cantidad_inicial` | 201; `stock_actual` 0 y estado `AGOTADO` |
| CP-HU02-03 | Crear con `cantidad_inicial` | 201; existe un movimiento ENTRADA con motivo `SALDO_INICIAL` |
| CP-HU02-04 | Código ya existente, también con otras mayúsculas (RN-01) | 409 `CODIGO_DUPLICADO` |
| CP-HU02-05 | Nombre vacío o sin categoría (RN-02) | 422 `DATOS_INVALIDOS` |
| CP-HU02-06 | `cantidad_inicial` con decimales en una unidad que no los admite (RN-04) | 422 `DATOS_INVALIDOS` |

**HU-03 / HU-04 · Consultar inventario y filtrar por categoría** · `GET /productos`, `GET /categorias` · tareas B4, B8, F5, F10

| ID | Condición | Esperado |
|---|---|---|
| CP-HU03-01 | Listar sin filtros | `{items,total,page,size}`; no incluye descontinuados |
| CP-HU03-02 | `incluir_descontinuados=true` | Incluye los descontinuados |
| CP-HU03-03 | `q` por código o nombre | Solo coincidencias |
| CP-HU03-04 | `estado=BAJO_STOCK` | Solo productos en ese estado |
| CP-HU03-05 | Paginación (`page`, `size`) | `total` constante y páginas sin repetidos |
| CP-HU03-06 | Fronteras de estado: stock 0, igual al mínimo, mínimo ± 0,001, sin mínimo, descontinuado | `AGOTADO`, `BAJO_STOCK`, `BAJO_STOCK`/`DISPONIBLE`, `DISPONIBLE`, `DESCONTINUADO` (RN-08..RN-11) |
| CP-HU04-01 | `GET /categorias` | Solo categorías activas |
| CP-HU04-02 | `GET /productos?categoria_id=X` | Solo productos de esa categoría |
| CP-HU03-07 | `GET /productos/{id}` inexistente | 404 `RECURSO_NO_EXISTE` |

**HU-05 · Editar producto** · `PATCH /productos/{id}` · tarea B9

| ID | Condición | Esperado |
|---|---|---|
| CP-HU05-01 | Editar con `If-Match` igual a la `version` actual | 200; `version` aumenta en 1 |
| CP-HU05-02 | Editar con `If-Match` desactualizado | 412 `VERSION_CONFLICTO` |
| CP-HU05-03 | Intentar cambiar `codigo` o `stock_actual` | No cambian |

**HU-12 · Descontinuar producto** · `/productos/{id}/descontinuar`, `/reactivar` · tarea B9

| ID | Condición | Esperado |
|---|---|---|
| CP-HU12-01 | Descontinuar | Estado `DESCONTINUADO`; conserva su historial (RN-11) |
| CP-HU12-02 | Reactivar | Vuelve al estado calculado por stock |
| CP-HU12-03 | `DELETE /productos/{id}` | 405 (RN-12) |

**Sin HU (catálogo y stock mínimo)** · tarea B9

| ID | Condición | Esperado |
|---|---|---|
| CP-RF16-01 | `PUT /productos/{id}/stock-minimo` con valor y con `null` (RN-14) | El estado se recalcula; `null` quita la alerta |
| CP-RNF09-01 | Crear y renombrar categoría (`POST`/`PATCH /categorias`) | 201/200; desactivada deja de salir en `GET /categorias` |

### Entrega 2 (cierra con R2)

**HU-06 · Registrar entrada** · `POST /movimientos/entradas` · tareas B10, F12

| ID | Condición | Esperado |
|---|---|---|
| CP-HU06-01 | Entrada `COMPRA` con `costo_unitario` y `proveedor_id` | 201; saldo nuevo y `costo_promedio_resultante` |
| CP-HU06-02 | Reintento con la misma `Idempotency-Key` | Devuelve el mismo movimiento; el saldo no cambia dos veces |
| CP-HU06-03 | Cantidad ≤ 0 o decimales no admitidos | 422 `DATOS_INVALIDOS` |
| CP-HU06-04 | Producto descontinuado | 409 `PRODUCTO_DESCONTINUADO` |

**HU-07 / HU-11 · Registrar salida o consumo** · `POST /movimientos/salidas` · tareas B10, F12

| ID | Condición | Esperado |
|---|---|---|
| CP-HU07-01 | Salida menor o igual al stock | 201; saldo y estado nuevos |
| CP-HU07-02 | Salida mayor al stock | 409 `STOCK_INSUFICIENTE`; el saldo no cambia |
| CP-HU07-03 | Dos salidas simultáneas por el último stock | Solo una se aplica; la otra recibe 409 |
| CP-HU11-01 | Salida que deja el producto en o bajo el mínimo | Estado `BAJO_STOCK` y aparece en `GET /alertas` |

**HU-08 · Historial de movimientos** · `GET /movimientos`, `GET /movimientos/{id}` · tareas B11, F13

| ID | Condición | Esperado |
|---|---|---|
| CP-HU08-01 | Filtros producto, tipo, usuario y fechas | Solo coincidencias |
| CP-HU08-02 | Manicurista lista movimientos | Solo los propios |
| CP-HU08-03 | Movimiento inexistente | 404 `RECURSO_NO_EXISTE` |

**HU-13 · Anular movimiento** · `POST /movimientos/{id}/anulaciones` · tareas B11, F13

| ID | Condición | Esperado |
|---|---|---|
| CP-HU13-01 | Anular un movimiento | Saldo revertido una sola vez (RN-13) |
| CP-HU13-02 | Anular de nuevo el mismo movimiento | 409 `MOVIMIENTO_YA_ANULADO` |
| CP-HU13-03 | `DELETE /movimientos/{id}` | 405 |

**HU-10 · Alertas de bajo stock** · `GET /alertas`, `GET /alertas/resumen` · tarea X4

| ID | Condición | Esperado |
|---|---|---|
| CP-HU10-01 | Productos `BAJO_STOCK` y `AGOTADO` | Aparecen con su faltante (mínimo − stock) |
| CP-HU10-02 | Producto sin mínimo (RN-14) | No genera alerta por bajo stock |
| CP-HU10-03 | Resumen | Conteo por estado igual al de `GET /productos?estado=…` |

**Sin HU (analítica, geografía, recuperación)** · tareas B14, X2, X3, X5, X6, X7

| ID | Condición | Esperado |
|---|---|---|
| CP-RF19-01 | `GET /analitica/tablero` | Indicadores coherentes con los datos de D11 |
| CP-RF14-01 | `GET /analitica/consumo` en un rango de fechas | Suma igual a las salidas del rango |
| CP-RF17-01 | `GET /analitica/cobertura` | Días de cobertura calculados con el consumo |
| CP-DEC11-01 | `GET /analitica/kardex` de un producto | Costo promedio ponderado igual al calculado a mano con el ejemplo de A3 |
| CP-RNF10-01 | `GET /analitica/exportar` | Archivo descargable con inventario o movimientos |
| CP-RF17-02 | `GET /analitica/proveedores-cercanos` con lat, lon y radio | GeoJSON solo con proveedores dentro del radio |
| CP-RF17-03 | `POST /proveedores` con NIT repetido | 409 |
| CP-REC-01 | `POST /auth/recuperar` con correo existente y no existente | 202 en ambos casos (no revela cuentas) |

## 4. Matriz de permisos convertida en casos 401/403

Cada fila es un caso automatizable. **401** = sin token o con token inválido. **✓** = el rol pasa el control de permiso (la respuesta no es 401 ni 403). **403** = `SIN_PERMISO`. Origen: permiso exigido según el contrato y permisos por rol según la sección 6 de la arquitectura.

| ID | Servicio | Endpoint | Permiso | Sin token | Administrador | Manicurista | Gerente | Decisión pendiente |
|---|---|---|---|---|---|---|---|---|
| PM-01 | analitica | `GET /alertas` | `alerta.consultar` | 401 | ✓ | ✓ | ✓ | DEC-04 |
| PM-02 | analitica | `GET /alertas/resumen` | `alerta.consultar` | 401 | ✓ | ✓ | ✓ | DEC-04 |
| PM-03 | analitica | `GET /analitica/tablero` | `analitica.consultar` | 401 | ✓ | 403 | ✓ |  |
| PM-04 | analitica | `GET /analitica/consumo` | `analitica.consultar` | 401 | ✓ | 403 | ✓ |  |
| PM-05 | analitica | `GET /analitica/cobertura` | `analitica.consultar` | 401 | ✓ | 403 | ✓ |  |
| PM-06 | analitica | `GET /analitica/exportar` | `analitica.consultar` | 401 | ✓ | 403 | ✓ |  |
| PM-07 | analitica | `GET /analitica/kardex` | `analitica.consultar` | 401 | ✓ | 403 | ✓ |  |
| PM-08 | analitica | `GET /analitica/proveedores-cercanos` | `alerta.consultar` | 401 | ✓ | ✓ | ✓ | DEC-04 |
| PM-09 | catalogo | `GET /categorias` | `producto.consultar` | 401 | ✓ | ✓ | ✓ |  |
| PM-10 | catalogo | `POST /categorias` | `catalogo.administrar` | 401 | ✓ | 403 | 403 |  |
| PM-11 | catalogo | `PATCH /categorias/{categoria_id}` | `catalogo.administrar` | 401 | ✓ | 403 | 403 |  |
| PM-12 | catalogo | `GET /unidades-medida` | `producto.consultar` | 401 | ✓ | ✓ | ✓ |  |
| PM-13 | catalogo | `GET /productos` | `producto.consultar` | 401 | ✓ | ✓ | ✓ |  |
| PM-14 | catalogo | `POST /productos` | `producto.crear` | 401 | ✓ | 403 | 403 |  |
| PM-15 | catalogo | `GET /productos/{producto_id}` | `producto.consultar` | 401 | ✓ | ✓ | ✓ |  |
| PM-16 | catalogo | `PATCH /productos/{producto_id}` | `producto.editar` | 401 | ✓ | 403 | 403 |  |
| PM-17 | catalogo | `PUT /productos/{producto_id}/stock-minimo` | `producto.configurar_minimo` | 401 | ✓ | 403 | 403 |  |
| PM-18 | catalogo | `POST /productos/{producto_id}/descontinuar` | `producto.descontinuar` | 401 | ✓ | 403 | 403 |  |
| PM-19 | catalogo | `POST /productos/{producto_id}/reactivar` | `producto.descontinuar` | 401 | ✓ | 403 | 403 |  |
| PM-20 | catalogo | `GET /proveedores` | `producto.consultar` | 401 | ✓ | ✓ | ✓ |  |
| PM-21 | catalogo | `POST /proveedores` | `catalogo.administrar` | 401 | ✓ | 403 | 403 |  |
| PM-22 | catalogo | `PATCH /proveedores/{proveedor_id}` | `catalogo.administrar` | 401 | ✓ | 403 | 403 |  |
| PM-23 | identidad | `POST /auth/login` | `Público` | — | — | — | — |  |
| PM-24 | identidad | `POST /auth/recuperar` | `Público` | — | — | — | — |  |
| PM-25 | identidad | `GET /auth/me` | `Autenticado` | 401 | ✓ | ✓ | ✓ |  |
| PM-26 | identidad | `GET /usuarios` | `usuario.gestionar` | 401 | ✓ | 403 | ✓ | DEC-02 (admin) · DEC-01 (gerente) |
| PM-27 | identidad | `POST /usuarios` | `usuario.gestionar` | 401 | ✓ | 403 | ✓ | DEC-02 (admin) · DEC-01 (gerente) |
| PM-28 | identidad | `GET /usuarios/{usuario_id}` | `usuario.gestionar` | 401 | ✓ | 403 | ✓ | DEC-02 (admin) · DEC-01 (gerente) |
| PM-29 | identidad | `PATCH /usuarios/{usuario_id}` | `usuario.gestionar` | 401 | ✓ | 403 | ✓ | DEC-02 (admin) · DEC-01 (gerente) |
| PM-30 | identidad | `PATCH /usuarios/{usuario_id}/estado` | `usuario.gestionar` | 401 | ✓ | 403 | ✓ | DEC-02 (admin) · DEC-01 (gerente) |
| PM-31 | identidad | `GET /roles` | `usuario.gestionar` | 401 | ✓ | 403 | ✓ | DEC-02 (admin) · DEC-01 (gerente) |
| PM-32 | movimientos | `GET /motivos-movimiento` | `movimiento.consultar` | 401 | ✓ | ✓ | ✓ |  |
| PM-33 | movimientos | `POST /movimientos/entradas` | `movimiento.registrar_entrada` | 401 | ✓ | 403 | 403 | DEC-03 |
| PM-34 | movimientos | `POST /movimientos/salidas` | `movimiento.registrar_salida` | 401 | ✓ | ✓ | 403 |  |
| PM-35 | movimientos | `GET /movimientos` | `movimiento.consultar` | 401 | ✓ | ✓ solo propios | ✓ |  |
| PM-36 | movimientos | `GET /movimientos/{movimiento_id}` | `movimiento.consultar` | 401 | ✓ | ✓ (¿solo propios? sin definir en el contrato) | ✓ |  |
| PM-37 | movimientos | `POST /movimientos/{movimiento_id}/anulaciones` | `movimiento.anular` | 401 | ✓ | 403 | 403 |  |

Las filas con «Decisión pendiente» dependen de A1. Mientras el grupo no decida, rige el valor de la tabla, como establece la sección 6. Si A1 cambia alguna decisión, se actualizan esta tabla y las pruebas en el mismo PR.

**Regla de ejecución:** los casos «Sin token» se pueden correr desde ya contra staging, porque el andamiaje ya exige permiso en los 37 endpoints. Los casos por rol requieren los usuarios de prueba de la sección 2.

## 5. Criterios de entrada y salida por entrega

### Entrega 1 · release 0.1.0 (R1)

**Entrada a pruebas:** B4, B5, B6, B8 y B9 fusionadas en `develop` y desplegadas en staging; D5 en staging; usuarios de prueba creados.

**Salida (todas se deben cumplir para que QA certifique R1):**
1. Casos CP-HU01, CP-HU09, CP-HU02, CP-HU03/04, CP-HU05, CP-HU12, CP-RF16 y CP-RNF09 en verde contra staging (Q2).
2. Filas PM de identidad y catálogo en verde para los 3 roles.
3. Ningún endpoint de la Entrega 1 responde 501 `NO_IMPLEMENTADO`.
4. Checks `calidad / pipeline` y `seguridad / scan` en verde en `develop` de los 3 repositorios.
5. Cero defectos críticos o altos abiertos.
6. Producción verificada después del despliegue: login y consulta del catálogo (criterio de R1).

### Entrega 2 · release 1.0.0 (R2)

**Entrada a pruebas:** B10, B11, B14 y X1..X7 fusionadas; D7, D9, D11 y D12 en staging.

**Salida:**
1. Todos los casos de la sección 3 en verde (Q2 + Q4).
2. Las 37 filas PM en verde para los 3 roles.
3. E2E de Q3 en verde para Administrador y Manicurista contra el Preview de Vercel.
4. Q5: escenario de 20 usuarios con informe de p95 y errores contra staging.
5. Cero respuestas 501 en toda la API (criterio de B12).
6. Cero defectos críticos o altos abiertos; los medios, con fecha de corrección acordada.

## 6. Gestión de defectos

| Severidad | Definición | Bloquea la release |
|---|---|---|
| Crítica | Pérdida o corrupción de datos, saldo incorrecto, acceso sin permiso | Sí |
| Alta | Una HU de la entrega no se puede completar | Sí |
| Media | La HU se completa con un rodeo o un mensaje incorrecto | No, con fecha de corrección |
| Baja | Cosmético | No |

Cada defecto se registra como issue en el repositorio del componente, con el ID del caso (CP-… o PM-…), los pasos, el resultado esperado y el obtenido, y se enlaza al issue de la tarea.

## 7. Inconsistencias detectadas al preparar este plan

Verificadas el 31-oct-2026. Cada una debe corregirse con un PR de su responsable:

| # | Inconsistencia | Evidencia | Acción |
|---|---|---|---|
| 1 | La prueba de ejemplo de login envía `{"usuario","clave"}`, pero el contrato exige `correo` y `contrasena` | `suites/api/test_salud.py` contra `LoginEntrada` en `identidad/api/esquemas.py` | QA la corrige en Q2 |
| 2 | La estrategia dice que la carga se prueba con k6; la tarea Q5 dice Locust | `docs/ESTRATEGIA_QA.md` contra el issue Q5 | Definirlo en Q5 y alinear ambos textos |
| 3 | Los issues del plan anuncian un «seguimiento automático» que no existe | `gh workflow list` en spa-org-bootstrap: solo `ci`, `Dependabot Updates` y `Dependency Graph` | Corregir el texto de los issues o instalar el seguimiento |
| 4 | Cuatro permisos dependen de decisiones sin ratificar (DEC-01..04) | Sección 6 de la arquitectura; issue A1 abierto | A1 |
| 5 | El contrato no define si la Manicurista puede ver el detalle de movimientos ajenos (`GET /movimientos/{id}`) | Contrato de movimientos: solo la lista dice «solo los propios» | Definirlo en B11 y actualizar PM-36 |
