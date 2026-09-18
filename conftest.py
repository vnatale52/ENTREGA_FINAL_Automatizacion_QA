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
    """Hook que captura automáticamente una pantalla si la prueba falla."""
    outcome = yield
    report = outcome.get_result()
    extras = getattr(report, "extras", [])

    if report.when == "call" and report.failed:
        driver_instance = getattr(item, "driver", None)
        if driver_instance:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_name = item.name.replace("[", "_").replace("]", "_")
            screenshot_name = f"{clean_name}_{timestamp}.png"
            screenshot_path = SCREENSHOTS_DIR / screenshot_name

            try:
                driver_instance.save_screenshot(str(screenshot_path))
                logger.error(f"Captura de pantalla de fallo guardada en: {screenshot_path}")

                pytest_html = item.config.pluginmanager.getplugin("html")
                if pytest_html:
                    import base64
                    with open(screenshot_path, "rb") as img_file:
                        encoded = base64.b64encode(img_file.read()).decode("utf-8")
                    extras.append(pytest_html.extras.png(encoded))
            except Exception as e:
                logger.warning(f"No se pudo capturar la pantalla: {e}")

    report.extras = extras


def pytest_html_report_title(report):
    """Personaliza el título del reporte HTML generado."""
    report.title = "Reporte de Pruebas Automatizadas - SauceDemo (Pre-Entrega QA)"
