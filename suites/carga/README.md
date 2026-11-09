# Q5 · Prueba de carga de inventario y salidas

Escenario k6 contra staging para RNF-04 / DEC-07. Cada ejecución usa 20 usuarios virtuales y 20 iteraciones totales. Cada iteración consulta el inventario de un producto QA y registra una salida de ese producto.

## Criterios

- p95 de las solicitudes y de cada operación menor o igual a 1.500 ms.
- Tasa de respuestas HTTP fallidas y de errores funcionales menor o igual a 1 %.
- 20/20 consultas y 20/20 salidas exitosas para considerar completo el escenario.

## Preparar datos y secretos

Solicita a QA la URL base de staging, un usuario Administrador de pruebas y el UUID de un producto preparado para carga. El producto debe tener stock disponible para cubrir al menos `20 × QA_CANTIDAD_SALIDA`; cada corrida descuenta ese total y deja 20 movimientos en staging. No uses un producto real de operación.

Configura estas variables en la terminal, sin escribir sus valores en este archivo ni en el repositorio:

| Variable | Uso |
|---|---|
| `API_BASE_URL` | Origen de staging, por ejemplo `https://staging.example.test` (sin `/api/v1`) |
| `QA_ADMIN_CORREO` | Correo del usuario Administrador de QA |
| `QA_ADMIN_CONTRASENA` | Contraseña del usuario Administrador de QA |
| `QA_PRODUCTO_ID` | UUID del producto QA con stock reservado |
| `QA_CANTIDAD_SALIDA` | Cantidad por salida; opcional, por defecto `1` |
| `QA_MOTIVO_CODIGO` | Motivo de salida activo; opcional, por defecto `CONSUMO_SERVICIO` |

## Ejecutar

Desde la raíz del repositorio:

```sh
k6 run --summary-export=q5-summary.json suites/carga/q5_inventario_salidas.js
```

k6 devuelve código distinto de cero si incumple cualquiera de los umbrales. Guarda el resumen de salida y `q5-summary.json` como evidencia de Q5; el JSON no contiene credenciales.

## Registrar resultados

En el informe/PR, anota fecha y hora, URL/entorno (sin secretos), versión desplegada, 20 VUs, iteraciones completadas, p95 global y por operación, tasa de errores y cantidad de operaciones HTTP exitosas. Adjunta `q5-summary.json` y concluye si se cumplieron los límites DEC-07.
