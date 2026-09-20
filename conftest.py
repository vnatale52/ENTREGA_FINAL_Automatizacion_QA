import io
import json
import logging
import os
import sys
import pytest
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from utils.config import BASE_DIR, SCREENSHOTS_DIR

# Forzar codificación UTF-8 en streams estándar y entorno para evitar caracteres corruptos (mojibake)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

logger = logging.getLogger(__name__)


def pytest_configure(config):
    """Asegura la codificación UTF-8 durante toda la sesión de Pytest."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def pytest_addoption(parser):
    """Permite configurar parámetros de ejecución desde la línea de comandos."""
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Ejecutar el navegador Chrome en modo headless (sin interfaz gráfica)."
    )


@pytest.fixture(scope="session")
def test_data():
    """Carga los datos de prueba desde el archivo JSON centralizado."""
    data_path = BASE_DIR / "datos" / "test_data.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="function")
def driver(request):
    """Inicializa y destruye la instancia de WebDriver para cada test.

    Garantiza la total independencia entre casos de prueba.
    """
    is_headless = request.config.getoption("--headless")

    options = ChromeOptions()
    if is_headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")

    logger.info("Iniciando instancia de Chrome WebDriver...")
    browser = webdriver.Chrome(options=options)
    browser.maximize_window()

    # Inyección para que el hook de screenshot acceda al driver en caso de fallo
    request.node.driver = browser

    yield browser

    logger.info("Cerrando sesión de WebDriver...")
    browser.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook que procesa cada caso de prueba, asociando descripción, capturas de pantalla
    y detalles HTML enriquecidos al reporte de Pytest.
    """
    outcome = yield
    report = outcome.get_result()
    extras = getattr(report, "extras", [])

    if report.when == "call":
        # Extraer docstring descriptivo para mostrar en la tabla y tarjeta
        doc = getattr(item.function, "__doc__", "") or ""
        doc_lines = [line.strip() for line in doc.splitlines() if line.strip()]
        first_line = doc_lines[0] if doc_lines else item.name
        report.description = first_line

        pytest_html = item.config.pluginmanager.getplugin("html")
        driver_instance = getattr(item, "driver", None)

        # Captura de pantalla de evidencia (tanto para éxito como para fallo)
        if driver_instance:
            status_label = "PASSED" if report.passed else "FAILED"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_name = item.name.replace("[", "_").replace("]", "_")
            screenshot_name = f"{clean_name}_{status_label}_{timestamp}.png"
            screenshot_path = SCREENSHOTS_DIR / screenshot_name

            try:
                driver_instance.save_screenshot(str(screenshot_path))
                if pytest_html:
                    import base64
                    with open(screenshot_path, "rb") as img_file:
                        encoded = base64.b64encode(img_file.read()).decode("utf-8")
                    caption = f"Evidencia Visual ({status_label}): {first_line}"
                    extras.append(pytest_html.extras.png(encoded, name=caption))
            except Exception as e:
                logger.warning(f"No se pudo capturar la pantalla: {e}")

        # Agregar tarjeta de detalles HTML con las consignas y pasos del test
        if pytest_html and doc_lines:
            body_lines = "\n".join(doc_lines[1:]) if len(doc_lines) > 1 else "Ejecución completada."
            badge_color = "#28a745" if report.passed else "#dc3545"
            status_text = "APROBADO" if report.passed else "FALLIDO"
            details_html = f"""
            <div style="margin: 8px 0; padding: 12px; background: #ffffff; border-left: 5px solid {badge_color}; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <strong style="color: #2c3e50; font-size: 13px;">📋 {first_line}</strong>
                    <span style="background: {badge_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{status_text}</span>
                </div>
                <pre style="margin: 0; background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 11px; line-height: 1.5; color: #495057; white-space: pre-wrap;">{body_lines}</pre>
            </div>
            """
            extras.append(pytest_html.extras.html(details_html))

    report.extras = extras


def pytest_html_results_table_header(cells):
    """Inserta una columna descriptiva en el encabezado de la tabla de resultados."""
    cells.insert(2, '<th class="sortable">Descripción</th>')


def pytest_html_results_table_row(report, cells):
    """Inserta la descripción correspondiente a cada caso de prueba en la tabla."""
    desc = getattr(report, "description", "")
    cells.insert(2, f"<td><strong>{desc}</strong></td>")


def pytest_html_results_summary(prefix, summary, postfix, session):
    """Añade un banner ejecutivo al inicio del reporte con los datos del estudiante y proyecto."""
    prefix.extend([
        '<div style="margin: 15px 0 20px 0; padding: 16px; background: #f4fbf7; border: 1px solid #c3e6cb; border-radius: 8px; font-family: \'Segoe UI\', sans-serif;">',
        '<h2 style="margin: 0 0 10px 0; color: #155724; font-size: 18px;">🎓 Pre-Entrega de Automatización QA - SauceDemo</h2>',
        '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 8px; font-size: 12px; color: #1e4620;">',
        '<div>👤 <strong>Estudiante / Autor:</strong> Vincenzo Natale</div>',
        '<div>🎯 <strong>Sistema Evaluado:</strong> <a href="https://www.saucedemo.com" target="_blank" style="color:#0056b3;">SauceDemo E-commerce</a></div>',
        '<div>🛠️ <strong>Stack Técnico:</strong> Python 3.13, Selenium 4.20+, Pytest 8.3</div>',
        '<div>📐 <strong>Patrón de Diseño:</strong> Page Object Model (POM) con esperas explícitas</div>',
        '</div>',
        '</div>'
    ])


def pytest_html_report_title(report):
    """Personaliza el título de la pestaña y encabezado del reporte HTML."""
    report.title = "Reporte de Pruebas Automatizadas - SauceDemo (Pre-Entrega QA de Vincenzo Natale)"
