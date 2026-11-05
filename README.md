# Entrega Final de Proyecto: Framework de Automatización de Pruebas QA (UI + API)
**Estudiante / Autor:** Vincenzo Natale

Framework integral de automatización de pruebas desarrollado para el **Trabajo Final Integrador** del curso de **Automation Testing**. Combina pruebas funcionales End-to-End de interfaz de usuario (**Selenium WebDriver** sobre [SauceDemo](https://www.saucedemo.com/)) aplicando el patrón **Page Object Model (POM)** y pruebas de integración backend sobre una API REST pública (**Requests** sobre [JSONPlaceholder](https://jsonplaceholder.typicode.com/)), junto con manejo de datos externos (**CSV, JSON y Faker**), logging centralizado rotativo, capturas de pantalla automáticas, reportes HTML ejecutivos e integración continua con **GitHub Actions**.

---

## 🎯 Propósito del Proyecto

El propósito de este proyecto es proporcionar una arquitectura de pruebas automatizadas escalable, mantenible y reproducible que permita validar tanto el frontend como el backend de una aplicación web moderna. Sus objetivos principales son:

- **Separación de responsabilidades con Page Object Model (POM):** Aislar los localizadores y las acciones de cada página (`pages/`) de la lógica de validación de los casos de prueba (`tests/`).
- **Enfoque Data-Driven Testing (DDT) e Híbrido:** Parametrizar las pruebas con `@pytest.mark.parametrize` leyendo datos fijos desde fuentes externas (`datos/login.csv`, `datos/productos.json`, `datos/test_data.json`) y generando datos dinámicos realistas mediante `Faker`.
- **Cobertura Multicapa (UI + API REST):** Validar flujos completos de negocio en la interfaz web (login, filtros de catálogo, carrito, checkout y escenarios negativos) y certificar el ciclo de vida CRUD de endpoints HTTP (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) con encadenamiento de peticiones y validación en 5 niveles (código de estado, cabeceras, esquema JSON, contenido y tiempo de respuesta).
- **Independencia y Estabilidad:** Garantizar que cada prueba se ejecute en un entorno limpio mediante fixtures con *teardown* automático y esperas explícitas (`WebDriverWait`).
- **Observabilidad y Trazabilidad Completa:** Generar un reporte visual autocontenido (`reports/reporte.html`) con métricas ejecutivas (KPIs), capturas de pantalla automáticas con fecha/hora (`reports/screenshots/`) y un registro histórico detallado paso a paso (`logs/suite.log`).

---

## 🛠️ Tecnologías Utilizadas

| Tecnología / Biblioteca | Versión | Propósito en el Framework |
|---|---|---|
| **Python** | 3.12+ / 3.13 | Lenguaje de programación principal del proyecto |
| **Pytest** | 8.0+ / 9.x | Motor de ejecución de pruebas, fixtures, marcadores (`markers`) y parametrización |
| **Selenium WebDriver** | 4.20+ | Automatización de pruebas de interfaz gráfica (UI) en Google Chrome |
| **Requests** | 2.31+ | Cliente HTTP para automatización de pruebas de API REST |
| **Faker** | 24.0+ | Generación de datos dinámicos y aleatorios para formularios de Checkout y payloads de API |
| **pytest-html** | 4.0+ | Generación de reportes HTML detallados y autocontenidos (`--self-contained-html`) |
| **pytest-check** | 2.0+ | Soporte para aserciones múltiples (*soft-asserts*) |
| **pytest-rerunfailures** | 14.0+ | Reintentos automáticos ante fallos intermitentes de red |
| **Git & GitHub Actions** | CI/CD | Control de versiones local/remoto y pipeline de ejecución continua |

---

## 📁 Estructura del Proyecto

El código está organizado de manera modular siguiendo las mejores prácticas de ingeniería de calidad:

```text
ENTREGA_FINAL_Automatizacion_QA/
├── .github/
│   └── workflows/
│       └── ci_tests.yml                # Pipeline de CI/CD en GitHub Actions
├── .gitignore                          # Exclusión de entorno virtual, cachés y temporales
├── requirements.txt                    # Lista de dependencias del framework
├── pytest.ini                          # Configuración de Pytest, marcadores y reporte HTML
├── conftest.py                         # Fixtures globales, captura de screenshots y dashboard HTML
├── pages/                              # Clases Page Object Model (POM) para pruebas de UI
│   ├── __init__.py
│   ├── base_page.py                    # Clase base con esperas explícitas (WebDriverWait)
│   ├── login_page.py                   # Página de autenticación y validación de errores
│   ├── inventory_page.py               # Página de catálogo, filtros de ordenamiento y carrito
│   ├── cart_page.py                    # Página del carrito de compras y eliminación de ítems
│   └── checkout_page.py                # Página del flujo de Checkout (Pasos 1, 2 y Confirmación)
├── utils/                              # Utilidades, configuración, datos y logging
│   ├── __init__.py
│   ├── config.py                       # URLs base, timeouts y rutas de directorios
│   ├── logger.py                       # Sistema de logging rotativo en UTF-8 (logs/suite.log)
│   ├── datos.py                        # Lectores de CSV/JSON y generadores con Faker
│   └── api_utils.py                    # Validador reutilizable de 5 niveles para respuestas API
├── datos/                              # Fuentes externas de datos de prueba (Data-Driven)
│   ├── login.csv                       # Credenciales válidas e inválidas para login parametrizado
│   ├── productos.json                  # Catálogo de productos para pruebas parametrizadas de carrito
│   └── test_data.json                  # Datos esperados de UI y payloads de prueba para API
├── tests/                              # Suites de casos de prueba automatizados (UI + API)
│   ├── __init__.py
│   ├── test_saucedemo.py               # Suite de pruebas de UI (8 funciones / 14 ejecuciones)
│   └── test_api_jsonplaceholder.py     # Suite de pruebas de API REST (7 funciones / 8 ejecuciones)
├── reports/                            # Reportes y evidencias visuales generadas
│   ├── reporte.html                    # Reporte HTML ejecutivo autocontenido
│   └── screenshots/                    # Capturas de pantalla automáticas con nombre y timestamp
├── logs/                               # Archivos de registro de ejecución
│   └── suite.log                       # Log cronológico detallado de toda la suite
└── README.md                           # Documentación técnica del proyecto
```

---

## 🧪 Cobertura de Casos de Prueba

### 1. Pruebas de Interfaz de Usuario - UI (`tests/test_saucedemo.py`)
Implementan el patrón **Page Object Model**, parametrización con **CSV y JSON**, datos dinámicos con **Faker** y escenarios tanto positivos como negativos:

| ID | Función de Prueba | Tipo / Fuente de Datos | Descripción y Validaciones |
|---|---|---|---|
| **UI-01** | `test_01_login_exitoso` | Positivo (JSON) | Inicia sesión con `standard_user` y valida redirección a `/inventory.html`, encabezado `"Products"` y logo `"Swag Labs"`. |
| **UI-02** | `test_02_login_parametrizado_csv` | Positivo y 4 Negativos (`datos/login.csv`) | Ejecuta 5 combinaciones desde CSV (`standard_user`, `locked_out_user`, credenciales inválidas, usuario vacío y clave vacía), verificando redirección o mensaje de error exacto (`Epic sadface:...`). |
| **UI-03** | `test_03_navegacion_y_filtro_catalogo` | Funcional (Catálogo) | Verifica elementos clave de la interfaz y prueba el selector de ordenamiento por precio ascendente (`lohi`) y descendente (`hilo`), comprobando el orden numérico de los precios. |
| **UI-04** | `test_04_agregar_producto_carrito` | Funcional (Carrito) | Añade el primer producto del catálogo, verifica que el contador del carrito suba a `1` y comprueba nombre, precio y cantidad en `/cart.html`. |
| **UI-05** | `test_05_carrito_parametrizado_json` | Data-Driven (`datos/productos.json`) | Ejecuta 3 pruebas parametrizadas agregando cada producto del archivo JSON por su nombre exacto y validando sus datos en el carrito. |
| **UI-06** | `test_06_eliminar_producto_carrito` | Funcional (Carrito) | Agrega un producto al carrito, navega a `/cart.html`, lo elimina con el botón `Remove` y comprueba que el carrito quede vacío (`0` ítems). |
| **UI-07** | `test_07_flujo_completo_checkout_e2e` | End-to-End (`Faker`) | Completa una compra de principio a fin: Login -> Catálogo -> Carrito -> Formulario Checkout con datos generados por `Faker` -> Resumen de precios -> Confirmación `"Thank you for your order!"`. |
| **UI-08** | `test_08_checkout_campos_obligatorios_negativo` | Escenario Negativo | Intenta avanzar en el paso 1 del Checkout dejando el formulario vacío y valida el mensaje `"Error: First Name is required"`. |

### 2. Pruebas de API REST (`tests/test_api_jsonplaceholder.py`)
Utilizan la biblioteca `requests` y el validador `validate_api_response` de 5 niveles (Status Code, Header `Content-Type`, Esquema JSON, Contenido y Rendimiento):

| ID | Función de Prueba | Método HTTP | Descripción y Validaciones |
|---|---|---|---|
| **API-01** | `test_api_01_get_listar_usuarios` | `GET /users` | Verifica estado `200 OK`, cabecera JSON, lista no vacía y esquema completo (`id`, `name`, `username`, `email`, `address`, `company`). |
| **API-02** | `test_api_02_get_recurso_inexistente_negativo` | `GET /posts/999999` | Escenario negativo que verifica código `404 Not Found` y cuerpo JSON vacío `{}`. |
| **API-03** | `test_api_03_post_crear_recurso_parametrizado` | `POST /posts` | Prueba parametrizada (2 ejecuciones) que crea recursos, verifica estado `201 Created`, `id` generado y coincidencia del payload enviado. |
| **API-04** | `test_api_04_put_reemplazar_recurso_completo` | `PUT /posts/1` | Reemplaza íntegramente el recurso `#1`, verificando código `200 OK` y actualización de todos sus campos. |
| **API-05** | `test_api_05_patch_actualizar_recurso_parcial` | `PATCH /posts/1` | Actualiza parcialmente solo el campo `title`, verificando código `200 OK` y preservación de `body` y `userId`. |
| **API-06** | `test_api_06_delete_eliminar_recurso` | `DELETE /posts/1` | Elimina el recurso `#1`, validando código `200 OK` y respuesta vacía `{}`. |
| **API-07** | `test_api_07_flujo_encadenado_crud_completo` | `POST` -> `PATCH` -> `DELETE` | **Encadenamiento de peticiones:** Crea un post con `Faker`, toma el `id` devuelto para actualizar su título con `PATCH` y finalmente lo elimina con `DELETE`. |

---

## 🚀 ¿Cómo instalar las dependencias?

Abre una terminal de **Git Bash** (estándar POSIX) en tu equipo y sigue estos pasos:

### 1. Situarte en el directorio del proyecto
```bash
cd ~/Desktop/QA_Curso_Automatation_Testing/ENTREGA_FINAL_Automatizacion_QA
```

### 2. Crear y activar el entorno virtual
```bash
python -m venv venv
source venv/Scripts/activate
```

### 3. Instalar los paquetes requeridos
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## ▶️ ¿Cómo ejecutar las pruebas?

Gracias a la configuración centralizada en `pytest.ini`, al ejecutar `pytest` se corren automáticamente las suites de UI y API y se genera el reporte HTML en `reports/reporte.html`.

### Ejecutar toda la suite (UI + API) en modo Headless (recomendado):
```bash
pytest -v --headless
```

### Ejecutar toda la suite con ventana del navegador visible:
```bash
pytest -v
```

### Ejecutar selectivamente por tipo de prueba o marcador (`markers`):
```bash
# Ejecutar únicamente las pruebas de interfaz gráfica (UI - Selenium)
pytest -v -m ui --headless

# Ejecutar únicamente las pruebas de backend (API REST - Requests)
pytest -v -m api

# Ejecutar únicamente las pruebas críticas de humo (Smoke Tests)
pytest -v -m smoke --headless

# Ejecutar únicamente los escenarios negativos (UI + API)
pytest -v -m negative --headless

# Ejecutar únicamente los flujos completos End-to-End (Checkout UI + CRUD encadenado API)
pytest -v -m e2e --headless
```

### Ejecutar con reintentos automáticos ante microcortes de red:
```bash
pytest -v --headless --reruns 2 --reruns-delay 2
```

---

## 📊 ¿Cómo interpretar los reportes generados?

Al finalizar cualquier ejecución de Pytest, dispones de tres fuentes complementarias de evidencia:

### 1. Reporte HTML Ejecutivo (`reports/reporte.html`)
Puedes abrirlo directamente desde **Git Bash** ejecutando:
```bash
start reports/reporte.html
```
Dentro del reporte encontrarás:
- **Banner Ejecutivo con KPIs Dinámicos:** Muestra en la parte superior el total de pruebas ejecutadas, la cantidad y porcentaje de pruebas aprobadas (*Passed*), las pruebas fallidas (*Failed*) y el desglose exacto entre pruebas de **UI** y de **API**.
- **Tabla de Resultados Interactiva:** Incluye el resultado (`Passed` / `Failed`), el identificador del test (con sus parámetros si proviene de CSV o JSON), la columna **Descripción del Caso** y la duración en segundos.
- **Botones `Show all details` / `Hide all details`:** Por defecto, todos los detalles visuales se despliegan automáticamente al abrir el archivo; puedes contraerlos o expandirlos en cualquier momento con un clic.
- **Tarjetas de Evidencia Visual (UI y API):**
  - En cada prueba de **UI**, verás la lista de pasos validados y la **captura de pantalla de alta resolución** tomada al finalizar el test (o en el instante exacto del fallo).
  - En cada prueba de **API**, verás una tarjeta técnica con el método HTTP (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`), la URL invocada, el código de estado recibido vs. esperado, el tiempo de respuesta en milisegundos (`ms`), el *Request Payload* enviado y el *Response JSON* devuelto por el servidor.

### 2. Capturas de Pantalla (`reports/screenshots/`)
Cada captura se almacena automáticamente en `reports/screenshots/` con un nombre descriptivo que incluye el nombre del test, el resultado (`PASSED` o `FAILED`) y la marca de tiempo (`YYYYMMDD_HHMMSS.png`).

### 3. Archivo de Logs Detallado (`logs/suite.log`)
Puedes consultar el historial cronológico completo desde la terminal con:
```bash
cat logs/suite.log
```
Registra cada navegación, ingreso de texto, clic, petición HTTP, tiempo de respuesta y validación realizada durante la ejecución, facilitando la depuración inmediata ante cualquier anomalía.
