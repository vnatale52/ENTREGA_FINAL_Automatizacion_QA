# Entrega Final de Proyecto: Framework de Automatización de Pruebas QA (UI + API)
**Estudiante / Autor:** Vincenzo Natale

[![Suite de Pruebas Automatizadas QA (UI + API)](https://github.com/vnatale52/PRE-ENTREGA_Automatizacion_QA/actions/workflows/ci_tests.yml/badge.svg)](https://github.com/vnatale52/PRE-ENTREGA_Automatizacion_QA/actions/workflows/ci_tests.yml)

Framework integral de automatización de pruebas desarrollado para el **Trabajo Final Integrador** del curso de **Automation Testing**. Combina pruebas funcionales End-to-End de interfaz de usuario (**Selenium WebDriver** sobre [SauceDemo](https://www.saucedemo.com/)) aplicando el patrón **Page Object Model (POM)** y pruebas de integración backend sobre una API REST pública (**Requests** sobre [JSONPlaceholder](https://jsonplaceholder.typicode.com/)), junto con manejo de datos externos (**CSV, JSON y Faker**), logging centralizado rotativo, capturas de pantalla automáticas, reportes HTML ejecutivos e integración continua con **GitHub Actions**.

---

## 🎯 Propósito del Proyecto

El propósito principal de este proyecto es construir y demostrar un **framework de automatización de pruebas de grado profesional**, capaz de certificar la calidad funcional y de integración de una aplicación web moderna tanto en su capa de presentación (**Frontend / UI**) como en su capa de servicios (**Backend / API REST**).

Más allá de automatizar scripts aislados, el proyecto está diseñado bajo principios de ingeniería de software que garantizan **mantenibilidad, escalabilidad, legibilidad y resiliencia ante cambios**:

1. **Arquitectura desacoplada mediante Page Object Model (POM):**
   - Cada pantalla del sistema bajo prueba ([SauceDemo](https://www.saucedemo.com/)) está representada por una clase dedicada dentro del paquete `pages/` (`LoginPage`, `InventoryPage`, `CartPage` y `CheckoutPage`), que hereda métodos de interacción seguros desde `BasePage`.
   - Los archivos de prueba en `tests/` contienen únicamente la lógica del caso de negocio y las aserciones (`assert`), sin incluir llamadas directas a `driver.find_element(...)`. Si un selector cambia en la interfaz gráfica, solo debes actualizarlo en un único lugar dentro de su Page Object correspondiente.

2. **Estrategia robusta y descriptiva de Localizadores Web (Locators):**
   - La selección de elementos del DOM sigue una jerarquía estricta de estabilidad y velocidad de resolución para evitar pruebas frágiles (*flaky tests*), prescindiendo de rutas XPath absolutas y priorizando identificadores únicos y atributos de prueba:
     - **`By.ID` (Máxima prioridad y rendimiento):** Utilizado siempre que el elemento posee un identificador único en el DOM, como los campos de autenticación (`id="user-name"`, `id="password"`, `id="login-button"`), el menú lateral (`id="react-burger-menu-btn"`), los botones de navegación del carrito (`id="checkout"`, `id="continue-shopping"`) y los controles del formulario de compra (`id="first-name"`, `id="last-name"`, `id="postal-code"`, `id="continue"`, `id="finish"`).
     - **`By.CSS_SELECTOR` con atributos semánticos (`data-test` y clases compuestas):** Empleado para capturar contenedores dinámicos diseñados específicamente para pruebas automatizadas, tales como los banners de mensajes de error (`[data-test='error']` tanto en Login como en Checkout) y los botones de acción contextual en tarjetas de producto (`button.btn_inventory`) o eliminación en el carrito (`button.cart_button`).
     - **`By.CLASS_NAME` (Agrupación estructural y colecciones de elementos):** Aplicado para localizar listas de elementos repetitivos o componentes de cabecera, como el listado de tarjetas del catálogo (`inventory_item`), nombres (`inventory_item_name`), precios (`inventory_item_price`), contador del carrito (`shopping_cart_badge`), selector de filtros (`product_sort_container`) y etiquetas de resumen financiero (`summary_subtotal_label`, `summary_total_label`, `complete-header`).

3. **Sincronización inteligente y Modo de Visualización Guiada (5 segundos):**
   - **Esperas explícitas (`WebDriverWait` + `expected_conditions`):** Todas las interacciones esperan dinámicamente a que los elementos sean visibles (`visibility_of_element_located`) o interactuables (`element_to_be_clickable`) hasta un umbral configurable (`DEFAULT_TIMEOUT = 10` segundos).
   - **Visualización de 5 segundos en modo ventana visible:** Cuando ejecutas la suite sin la bandera `--headless` (`pytest -v`), el fixture `driver` en `conftest.py` mantiene abierta cada ventana del navegador durante **5 segundos** al finalizar la prueba antes de ejecutar el cierre (`browser.quit()`), permitiéndote observar con claridad el estado final alcanzado en pantalla en cada escenario. En modo `--headless`, la suite omite esa pausa visual para ejecutarse a máxima velocidad en pipelines CI/CD.

4. **Enfoque Data-Driven Testing (DDT) e Híbrido (CSV + JSON + Faker):**
   - Los datos de prueba están completamente separados del código fuente y se inyectan mediante `@pytest.mark.parametrize`:
     - **Datos tabulares en CSV (`datos/login.csv`):** Almacena múltiples combinaciones de credenciales (usuarios válidos, usuarios bloqueados, credenciales inexistentes y campos vacíos) junto con el mensaje de error exacto esperado, etiquetando dinámicamente los casos negativos con el marcador `@pytest.mark.negative`.
     - **Estructuras jerárquicas en JSON (`datos/productos.json` y `datos/test_data.json`):** Define el catálogo de productos a verificar en el carrito (nombre exacto, precio con formato de moneda y descripción), los textos esperados en cada etapa de la UI y los payloads base para la API.
     - **Datos sintéticos dinámicos con `Faker`:** Genera nombres, apellidos y códigos postales realistas en español (`es_ES`) en cada ejecución del flujo E2E de Checkout, así como títulos y contenidos aleatorios para la creación de recursos vía API REST.

5. **Validación multicapa de API REST (5 niveles) y Encadenamiento CRUD:**
   - Las pruebas de backend sobre `JSONPlaceholder` emplean el validador centralizado `validate_api_response` (`utils/api_utils.py`), que inspecciona cada respuesta HTTP en **5 capas de control**: (1) código de estado HTTP (`200`, `201`, `404`), (2) cabeceras `Content-Type: application/json`, (3) integridad del esquema JSON mediante operaciones de conjuntos, (4) reglas de negocio sobre los datos devueltos y (5) tiempo de respuesta inferior al umbral de rendimiento (`< 3.0s`).
   - Incluye pruebas unitarias por verbo HTTP (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) y un flujo de **encadenamiento de peticiones** que simula el ciclo de vida real de un recurso (`POST` para crear → captura del `id` generado → `PATCH` para actualizar → `DELETE` para eliminar).

6. **Observabilidad, Evidencia Visual Automática y Auditoría en Logs:**
   - Cada ejecución genera un reporte ejecutivo autocontenido (`reports/reporte.html`) con un **Dashboard de KPIs dinámicos**, capturas de pantalla automáticas incrustadas en Base64 para todas las pruebas de UI (tanto aprobadas como fallidas, guardadas además en `reports/screenshots/` con fecha y hora), tarjetas detalladas con el *Request Payload* y *Response JSON* para todas las pruebas de API, y un archivo de registro rotativo en UTF-8 (`logs/suite.log`) que documenta cronológicamente cada paso.

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
├── conftest.py                         # Fixtures globales, pausa visual de 5s, screenshots y dashboard HTML
├── pages/                              # Clases Page Object Model (POM) para pruebas de UI
│   ├── __init__.py
│   ├── base_page.py                    # Clase base con esperas explícitas (WebDriverWait)
│   ├── login_page.py                   # Localizadores comentados y acciones de Login
│   ├── inventory_page.py               # Localizadores comentados, filtros y acciones de Catálogo
│   ├── cart_page.py                    # Localizadores comentados y acciones del Carrito
│   └── checkout_page.py                # Localizadores comentados del flujo de Checkout (Pasos 1, 2 y 3)
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
| **UI-07** | `test_07_flujo_completo_checkout_e2e` | End-to-End (`Faker`) | Completa una compra de principio a fin: Login → Catálogo → Carrito → Formulario Checkout con datos generados por `Faker` → Resumen de precios → Confirmación `"Thank you for your order!"`. |
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
| **API-07** | `test_api_07_flujo_encadenado_crud_completo` | `POST` → `PATCH` → `DELETE` | **Encadenamiento de peticiones:** Crea un post con `Faker`, toma el `id` devuelto para actualizar su título con `PATCH` y finalmente lo elimina con `DELETE`. |

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

### Ejecutar toda la suite con ventana del navegador visible (mostrando cada pantalla durante 5 segundos):
```bash
pytest -v
```

### Ejecutar toda la suite (UI + API) en modo Headless (sin interfaz gráfica, ejecución rápida):
```bash
pytest -v --headless
```

### Ejecutar selectivamente por tipo de prueba o marcador (`markers`):
```bash
# Ejecutar únicamente los escenarios negativos (4 Login CSV + 1 Checkout UI + 1 API 404 = 6 pruebas)
pytest -v -m negative --headless

# Ejecutar únicamente las pruebas de interfaz gráfica (UI - Selenium)
pytest -v -m ui --headless

# Ejecutar únicamente las pruebas de backend (API REST - Requests)
pytest -v -m api

# Ejecutar únicamente las pruebas críticas de humo (Smoke Tests)
pytest -v -m smoke --headless

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

---

## ⚙️ Estado de los Pipelines CI/CD en GitHub Actions

El proyecto cuenta con un pipeline de Integración Continua configurado en [`.github/workflows/ci_tests.yml`](./.github/workflows/ci_tests.yml) que se ejecuta automáticamente ante cada `push` o `pull_request` sobre la rama `main` (o de forma manual mediante `workflow_dispatch`).

| ID de Ejecución | Workflow | Commit (`main`) | Estado | Resultado | Enlace Directo |
|---|---|---|---|---|---|
| **`42204407513`** | `Suite de Pruebas Automatizadas QA (UI + API)` | `20e058b` *(Merge final)* | `completed` | ✅ **`success`** | [Ver Run #42204407513](https://github.com/vnatale52/PRE-ENTREGA_Automatizacion_QA/actions/runs/42204407513) |
| **`42200898865`** | `Suite de Pruebas Automatizadas QA (UI + API)` | `0ba1c74` | `completed` | ✅ **`success`** | [Ver Run #42200898865](https://github.com/vnatale52/PRE-ENTREGA_Automatizacion_QA/actions/runs/42200898865) |
| **`42200516855`** | `Suite de Pruebas Automatizadas QA (UI + API)` | `12c8468` | `completed` | ✅ **`success`** | [Ver Run #42200516855](https://github.com/vnatale52/PRE-ENTREGA_Automatizacion_QA/actions/runs/42200516855) |

### Etapas ejecutadas automáticamente en el contenedor (`ubuntu-latest`):
1. **Checkout del repositorio (`actions/checkout@v4`):** Descarga el código fuente actualizado de la rama.
2. **Entorno Python y caché (`actions/setup-python@v5`):** Configura Python 3.12 e instala las dependencias de `requirements.txt`.
3. **Navegador Google Chrome (`browser-actions/setup-chrome@v1`):** Instala Chrome estable para las pruebas de UI en modo `--headless`.
4. **Ejecución unificada de pruebas (`pytest`):** Corre las **22 pruebas automatizadas (14 UI + 8 API)** y genera el reporte autocontenido `reports/reporte.html`.
5. **Publicación de Artefactos (`actions/upload-artifact@v4`):** Empaqueta y almacena durante 30 días el artefacto descargable **`evidencias-qa-reporte-y-logs`** con `reports/reporte.html`, `reports/screenshots/` y `logs/suite.log`.

---

## 🌐 Serie de Comandos en Git Bash para Subir Todo al Repositorio Remoto en GitHub

Para sincronizar y publicar todos los cambios locales en el repositorio remoto de **GitHub**, abre tu terminal **Git Bash** y ejecuta la siguiente secuencia de comandos:

```bash
# 1. Situarte en la carpeta del proyecto
cd ~/Desktop/QA_Curso_Automatation_Testing/ENTREGA_FINAL_Automatizacion_QA

# 2. Verificar el estado del árbol de trabajo y la URL del repositorio remoto
git status
git remote -v

# 3. Agregar archivos modificados y registrar un commit descriptivo (si realizaste nuevos cambios)
git add .
git commit -m "feat: actualizar suite completa de Entrega Final QA (UI + API)"

# 4. Subir la rama principal (main) y la rama de desarrollo (feature/entrega-final) a GitHub
git push origin main
git push origin feature/entrega-final
```

