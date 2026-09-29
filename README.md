# QA Spa de Uñas - Pytest + Playwright

Módulo de aseguramiento de calidad del sistema de inventario de un spa de uñas. Contiene las pruebas de API, pruebas de extremo a extremo en navegador y pruebas de carga, trazadas a las historias de usuario. Funciona como puerta de calidad: los Pull Requests del backend y del frontend no se pueden fusionar si estas pruebas fallan.

## 🚀 Tecnologías Principales

* Pytest
* HTTPX (pruebas de API)
* Playwright para Python (pruebas E2E en navegador)
* k6 (pruebas de carga)

## ⚙️ Configuración del Entorno

### 1️⃣ Clonar el repositorio

```
git clone https://github.com/Proyecto-Maestria-Spa-Unas/spa-qa.git
cd spa-qa
git checkout develop
```

### 2️⃣ Crear entorno virtual (venv)

#### 🐧 Linux / Mac

```
python3 -m venv venv
source venv/bin/activate
```

#### 🪟 Windows (PowerShell)

```
python -m venv venv
venv\Scripts\Activate.ps1
```

Si da error de políticas:

```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 🪟 Windows (CMD)

```
python -m venv venv
venv\Scripts\activate.bat
```

### 3️⃣ Instalar dependencias

Con el entorno virtual activado:

```
pip install -r requirements.txt
pip install -r requirements-dev.txt
python -m playwright install chromium
```

✅ El comando es el mismo en todos los sistemas si el entorno está activado correctamente.

## ▶️ Ejecutar las pruebas

Primero levante los componentes a probar (backend en el puerto 8000 y frontend en el 5173). Luego:

#### 🐧 Linux / Mac

```
export API_BASE_URL=http://127.0.0.1:8000
export WEB_BASE_URL=http://localhost:5173
pytest suites
```

#### 🪟 Windows (PowerShell)

```
$env:API_BASE_URL="http://127.0.0.1:8000"
$env:WEB_BASE_URL="http://localhost:5173"
pytest suites
```

Ejecutar una sola suite o solo las pruebas funcionales:

```
pytest suites/api
pytest suites/web
pytest suites -m funcional
```

Si una URL no está definida, las pruebas que la necesitan se omiten (skip) en lugar de fallar.

## 📦 Dependencias Principales

### 🔹 Pytest
Motor de pruebas; organiza las suites y los marcadores de trazabilidad.

### 🔹 HTTPX
Cliente HTTP para probar los endpoints del backend.

### 🔹 pytest-playwright
Automatiza un navegador real para validar los flujos de la interfaz.

### 🔹 Herramientas de desarrollo (requirements-dev.txt)
ruff (lint y formato), mypy (tipos), pytest-cov y pip-audit.

## 🏷️ Trazabilidad con historias de usuario

Toda prueba funcional debe declarar la historia que valida. Si falta el marcador, la ejecución falla:

```python
@pytest.mark.funcional
@pytest.mark.hu("HU-07")
def test_no_permite_salida_mayor_al_stock(api_url):
    ...
```

Marcadores disponibles: `funcional`, `hu("HU-xx")`, `humo` (disponibilidad mínima) y `lento` (se excluye de la puerta de QA en los PR).

## 🔐 Variables de Entorno

| Variable | Uso |
|---|---|
| `API_BASE_URL` | URL base del backend bajo prueba |
| `WEB_BASE_URL` | URL base del frontend bajo prueba |

⚠️ No se deben guardar credenciales de usuarios de prueba en el código; se inyectan como variables de entorno o secretos de GitHub.

## 📁 Organización del proyecto

| Carpeta | Uso |
|---|---|
| `suites/api` | Pruebas funcionales y de contrato del backend. |
| `suites/web` | Pruebas E2E en navegador con Playwright. |
| `suites/carga` | Escenarios k6 de rendimiento (se ejecutan programados contra staging). |
| `suites/conftest.py` | URLs, fixtures compartidas y validación del marcador de historia de usuario. |
| `docs/ESTRATEGIA_QA.md` | Niveles de prueba, responsables y activación de la puerta de QA. |

## 🚦 Puerta de QA

Cuando la variable de organización `ENABLE_QA_GATE` está en `true`, cada Pull Request del backend ejecuta `suites/api` y cada Pull Request del frontend ejecuta `suites/web`. El check `qa-gate / qa` es obligatorio para fusionar.

## 🔀 Flujo de trabajo

1. Crear la rama desde `develop`: `git checkout -b test/HU-07-salidas`.
2. Abrir un Pull Request hacia `develop`.
3. El PR se fusiona cuando pasan `politica / pr` y `calidad / pipeline` y lo aprueba el equipo de QA.
