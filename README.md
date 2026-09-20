# Pre-Entrega: Automatización de Pruebas QA (SauceDemo)
**Autor:** Vincenzo Natale

Proyecto de automatización de pruebas web end-to-end (E2E) desarrollado para la **Pre-Entrega de Automatización de Testing (hasta Clase 8)**. El objetivo es validar los flujos críticos de autenticación, exploración de catálogo e interacción con el carrito de compras en la aplicación web [SauceDemo](https://www.saucedemo.com/).

---

## 🎯 Propósito del Proyecto

Demostrar la capacidad para diseñar, estructurar y ejecutar pruebas funcionales automatizadas robustas utilizando el patrón de diseño **Page Object Model (POM)**, garantizando:
- Separación clara entre la lógica de prueba y la interacción con la interfaz gráfica.
- Total independencia entre casos de prueba.
- Estrategia de esperas explícitas mediante `WebDriverWait` y `expected_conditions` (sin sleeps arbitrarios).
- Generación de reportes visuales en formato HTML (`pytest-html`) y captura automática de evidencias (screenshots) ante fallos.
- Registro continuo de logs descriptivos durante toda la ejecución.

---

## 🛠️ Tecnologías Utilizadas

- **Lenguaje:** Python 3.13+
- **Framework de Pruebas:** [Pytest](https://docs.pytest.org/) 8.3+
- **Automatización Web:** [Selenium WebDriver](https://www.selenium.dev/) 4.20+
- **Reportes:** [pytest-html](https://pytest-html.readthedocs.io/) 4.2+ (reportes HTML enriquecidos e independientes)
- **Navegador:** Google Chrome (con soporte para modo con interfaz gráfica o modo `--headless`)
- **Control de Versiones:** Git y GitHub

---

## 📁 Estructura del Proyecto

El proyecto está organizado de forma modular cumpliendo con las consignas del curso:

```text
pre-entrega-automation-testing-vincenzo-natale/
├── .gitignore                          # Exclusión de binarios, reportes generados y caches
├── requirements.txt                    # Dependencias del proyecto
├── pytest.ini                          # Configuración de Pytest, logs y marcadores
├── conftest.py                         # Fixtures de WebDriver y hook de screenshots ante fallos
├── pages/                              # Patrón Page Object Model (POM)
│   ├── __init__.py
│   ├── base_page.py                    # Clase base con esperas explícitas y métodos comunes
│   ├── login_page.py                   # Localizadores y acciones de la página de Login
│   ├── inventory_page.py               # Localizadores y acciones del Catálogo de Productos
│   └── cart_page.py                    # Localizadores y acciones del Carrito de Compras
├── utils/                              # Configuraciones y funciones auxiliares
│   ├── __init__.py
│   └── config.py                       # URLs, timeouts y rutas del sistema
├── datos/                              # Datos de prueba externos
│   └── test_data.json                  # Credenciales válidas y valores esperados
├── tests/                              # Casos de prueba automatizados
│   ├── __init__.py
│   └── test_saucedemo.py               # Pruebas de Login, Catálogo y Carrito
├── reports/                            # Evidencias de ejecución
│   ├── reporte.html                    # Reporte HTML generado por Pytest
│   └── screenshots/                    # Capturas de pantalla automáticas en caso de fallos
└── README.md                           # Documentación técnica del proyecto
```

---

## 🧪 Casos de Prueba Implementados

| ID | Caso de Prueba | Descripción | Criterios Mínimos Validados |
|---|---|---|---|
| **CP01** | `test_01_login_exitoso` | Inicio de sesión con credenciales válidas (`standard_user` / `secret_sauce`) | Espera explícita, redirección a `/inventory.html`, validación de título `"Products"` y logo `"Swag Labs"`. |
| **CP02** | `test_02_navegacion_catalogo` | Exploración del catálogo de inventario | Validación del título de sección, presencia de productos (mínimo 1), extracción de nombre y precio del primer ítem, verificación de menú hamburguesa, selector de filtros e ícono de carrito. |
| **CP03** | `test_03_agregar_producto_carrito` | Interacción con productos y validación del carrito | Agregar el primer producto al carrito, verificar incremento del badge a `1`, navegar a `/cart.html` y validar coincidencia de nombre, precio y cantidad (`1`). |

---

## 🚀 Instalación y Configuración (Git Bash / POSIX)

Abre una terminal de **Git Bash** y sigue estos pasos:

### 1. Clonar el repositorio
```bash
git clone https://github.com/[tu-usuario]/pre-entrega-automation-testing-vincenzo-natale.git
cd pre-entrega-automation-testing-vincenzo-natale
```

### 2. Crear y activar el entorno virtual
```bash
python -m venv venv
source venv/Scripts/activate
```

### 3. Instalar las dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ▶️ Ejecución de las Pruebas

Todas las ejecuciones utilizan sintaxis compatible con **Git Bash**.

### Ejecución estándar con navegador visible (modo normal):
```bash
pytest -v tests/test_saucedemo.py
```

### Ejecución en modo Headless (sin abrir ventana gráfica):
```bash
pytest -v tests/test_saucedemo.py --headless
```

### Generación de Reporte HTML (Consigna obligatoria):
Para generar el reporte HTML con todos los detalles y estadísticas de la ejecución:
```bash
pytest -v tests/test_saucedemo.py --headless --html=reporte.html --self-contained-html
```
*(También puedes generarlo dentro de la carpeta de reportes con `--html=reports/reporte.html`)*

### Ejecución por marcadores (tags):
```bash
# Ejecutar solo pruebas de humo
pytest -v -m smoke --headless

# Ejecutar solo la prueba de Login
pytest -v -m login --headless

# Ejecutar solo la prueba de Carrito
pytest -v -m cart --headless
```

---

## 📊 Reportes y Evidencias de Ejecución

1. **Reporte HTML:**
   - Una vez finalizada la ejecución con la bandera `--html=reporte.html`, abre el archivo en cualquier navegador web:
     ```bash
     start reporte.html
     ```
   - El reporte incluye: tiempo total de ejecución, detalles por paso, logs capturados por cada test y estado (Passed / Failed).

2. **Capturas de pantalla automáticas (Screenshots):**
   - El archivo `conftest.py` implementa el hook `pytest_runtest_makereport`. Si algún caso de prueba llega a fallar, automáticamente toma una captura del navegador con timestamp y la almacena en `reports/screenshots/`, incrustándola además en el reporte HTML.

3. **Logs de ejecución:**
   - La configuración en `pytest.ini` muestra en consola logs en tiempo real con timestamp, nivel de severidad y archivo emisor.

---

## 👥 Formato de Entrega del Curso

- **Estudiante / Autor:** Vincenzo Natale
- **Nombre del repositorio en GitHub:** `pre-entrega-automation-testing-vincenzo-natale`
- **Entregables:** Repositorio público en GitHub, archivo `README.md` completo, archivo `reporte.html` y commits descriptivos del progreso.
