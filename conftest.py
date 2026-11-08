import base64
import html
import importlib.metadata
import json
import logging
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage
from utils.config import (
    BASE_DIR,
    DEFAULT_BROWSER,
    SCREENSHOTS_DIR,
    VISUAL_DELAY_SECONDS,
)
from utils.logger import configure_file_logging

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

# Inicializar el sistema de logging centralizado en archivo (logs/suite.log)
configure_file_logging()
logger = logging.getLogger(__name__)

# Almacenamiento en memoria para estadísticas dinámicas del Dashboard HTML
_SESSION_RESULTS = []


def pytest_configure(config):
    """Asegura la codificación UTF-8 y el logger de archivo durante toda la sesión de Pytest."""
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
    configure_file_logging()
    _SESSION_RESULTS.clear()


@pytest.hookimpl(optionalhook=True)
def pytest_metadata(metadata):
    """Enriquece la fila 'Packages' de la tabla Environment en reporte.html con las bibliotecas clave del framework."""
    packages = metadata.setdefault("Packages", {})
    for dist_name, display_name in (
        ("selenium", "selenium"),
        ("requests", "requests"),
        ("pydantic", "pydantic"),
        ("python-dotenv", "python-dotenv"),
    ):
        try:
            packages[display_name] = importlib.metadata.version(dist_name)
        except Exception:
            pass


def pytest_addoption(parser):
    """Permite configurar parámetros de ejecución desde la línea de comandos (Mejoras 9.4 y 9.6)."""
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Ejecutar el navegador en modo headless (sin interfaz gráfica).",
    )
    parser.addoption(
        "--visual-delay",
        action="store",
        type=float,
        default=VISUAL_DELAY_SECONDS,
        help="Segundos de pausa visual al finalizar cada prueba con ventana visible (por defecto: 5).",
    )
    parser.addoption(
        "--browser",
        action="store",
        default=DEFAULT_BROWSER,
        choices=["chrome", "firefox", "edge"],
        help="Navegador objetivo para las pruebas de UI: chrome (default), firefox o edge.",
    )


@pytest.fixture(scope="session")
def test_data():
    """Carga los datos de prueba desde el archivo JSON centralizado."""
    data_path = BASE_DIR / "datos" / "test_data.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def api_client():
    """Inicializa una sesión HTTP persistente con Connection Pooling y Reintentos (Mejora 9.1).

    Reutiliza conexiones TCP/TLS (Keep-Alive) entre todas las pruebas de API REST
    y aplica una política de reintentos automáticos ante fallos transitorios (429, 500, 502, 503, 504).
    """
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=UTF-8",
            "User-Agent": "QA-Automation-Framework-VincenzoNatale/2.0",
        }
    )

    retry_strategy = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    logger.info("Sesión HTTP persistente (api_client con Keep-Alive y Retry) inicializada.")
    yield session
    logger.info("Cerrando sesión HTTP persistente (api_client)...")
    session.close()


def _create_webdriver(browser_name: str, is_headless: bool):
    """Fábrica multi-navegador para Chrome, Firefox y Edge (Mejora 9.6)."""
    browser_name = browser_name.lower()

    if browser_name == "firefox":
        options = FirefoxOptions()
        if is_headless:
            options.add_argument("--headless")
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")
        return webdriver.Firefox(options=options)

    if browser_name == "edge":
        options = EdgeOptions()
        if is_headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--inprivate")
        return webdriver.Edge(options=options)

    # Por defecto: Google Chrome
    options = ChromeOptions()
    if is_headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--incognito")
    options.add_argument("--disable-features=PasswordLeakDetection")
    options.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False,
        },
    )
    return webdriver.Chrome(options=options)


@pytest.fixture(scope="function")
def driver(request):
    """Inicializa y destruye la instancia de WebDriver para cada prueba de interfaz (UI).

    Garantiza la total independencia entre casos de prueba (Teardown limpio).
    Cuando se ejecuta con ventana visible (sin --headless), mantiene la ventana abierta
    durante 5 segundos por defecto (--visual-delay) al finalizar cada prueba.
    """
    is_headless = request.config.getoption("--headless")
    visual_delay = request.config.getoption("--visual-delay")
    browser_name = request.config.getoption("--browser")

    logger.info(f"Iniciando instancia de {browser_name.upper()} WebDriver para prueba UI...")
    browser = _create_webdriver(browser_name=browser_name, is_headless=is_headless)
    browser.maximize_window()

    # Inyección para que el hook de screenshot acceda al driver
    request.node.driver = browser

    yield browser

    if not is_headless and visual_delay > 0:
        logger.info(
            f"Manteniendo la ventana del navegador visible durante {visual_delay} segundos para su visualización..."
        )
        time.sleep(visual_delay)

    logger.info("Cerrando sesión de WebDriver (Teardown)...")
    browser.quit()


@pytest.fixture(scope="function")
def authenticated_inventory_page(driver, test_data) -> InventoryPage:
    """Fixture de sesión pre-autenticada para pruebas de Catálogo, Carrito y Checkout (Mejora 9.5).

    Aplica el principio DRY (Don't Repeat Yourself): autentica automáticamente al usuario
    válido ('standard_user') y devuelve la instancia de InventoryPage lista para operar.
    """
    user = test_data["valid_user"]
    logger.info(
        f"[Fixture Pre-Autenticado] Iniciando sesión automática con '{user['username']}'..."
    )
    LoginPage(driver).load().login(username=user["username"], password=user["password"])
    return InventoryPage(driver).wait_for_inventory_loaded()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook que procesa cada caso de prueba, capturando screenshots automáticamente
    (con nombre descriptivo y fecha/hora) e inyectando evidencia enriquecida para UI y API.
    """
    outcome = yield
    report = outcome.get_result()
    extras = getattr(report, "extras", [])

    if report.when == "call":
        doc = getattr(item.function, "__doc__", "") or ""
        doc_lines = [line.strip() for line in doc.splitlines() if line.strip()]
        first_line = doc_lines[0] if doc_lines else item.name
        report.description = first_line

        is_api_test = "api" in item.keywords
        report.test_category = "api" if is_api_test else "ui"
        _SESSION_RESULTS.append(
            {
                "passed": report.passed,
                "failed": report.failed,
                "skipped": report.skipped,
                "type": report.test_category,
            }
        )

        pytest_html = item.config.pluginmanager.getplugin("html")
        driver_instance = getattr(item, "driver", None)

        # 1. Gestión de Capturas de Pantalla (UI): almacena con fecha/hora y nombre del test
        if driver_instance:
            status_label = "PASSED" if report.passed else "FAILED"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_name = (
                item.name.replace("[", "_")
                .replace("]", "_")
                .replace("/", "_")
                .replace("\\", "_")
                .replace(":", "_")
            )
            screenshot_name = f"{clean_name}_{status_label}_{timestamp}.png"
            screenshot_path = SCREENSHOTS_DIR / screenshot_name

            try:
                driver_instance.save_screenshot(str(screenshot_path))
                if report.failed:
                    logger.error(f"Captura de pantalla por fallo guardada en: {screenshot_path}")
                else:
                    logger.info(f"Captura de evidencia visual guardada en: {screenshot_path}")

                if pytest_html:
                    with open(screenshot_path, "rb") as img_file:
                        encoded = base64.b64encode(img_file.read()).decode("utf-8")
                    caption = f"Evidencia Visual ({status_label}): {first_line}"
                    extras.append(pytest_html.extras.png(encoded, name=caption))
            except Exception as e:
                logger.warning(f"No se pudo capturar la pantalla: {e}")

        # 2. Tarjeta ejecutiva con pasos y validaciones del caso de prueba
        if pytest_html and doc_lines:
            body_lines = (
                "\n".join(doc_lines[1:])
                if len(doc_lines) > 1
                else "Ejecución completada satisfactoriamente."
            )
            badge_color = "#10b981" if report.passed else "#ef4444"
            status_text = "✔ APROBADO" if report.passed else "✖ FALLIDO"
            category_badge = "🌐 API REST (Requests)" if is_api_test else "🖥️ UI Web (Selenium)"

            details_html = f"""
            <div style="margin: 12px 0; padding: 16px; background: #ffffff; border-left: 6px solid {badge_color}; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 10px; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <span style="background: #e2e8f0; color: #0f172a; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; margin-right: 8px;">{category_badge}</span>
                        <span style="color: #0f172a; font-size: 15px; font-weight: 700;">📌 {html.escape(first_line)}</span>
                    </div>
                    <span style="background: {badge_color}; color: white; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px;">{status_text}</span>
                </div>
                <div style="font-size: 12px; color: #334155; line-height: 1.6;">
                    <pre style="margin: 0; background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-radius: 6px; font-family: Consolas, 'Courier New', monospace; font-size: 12px; line-height: 1.5; color: #1e293b; white-space: pre-wrap;">{html.escape(body_lines)}</pre>
                </div>
            </div>
            """
            extras.append(pytest_html.extras.html(details_html))

        # 3. Tarjeta de Evidencia Técnica para Pruebas de API (Request / Response JSON)
        api_evidences = getattr(item, "api_evidences", [])
        if pytest_html and api_evidences:
            method_colors = {
                "GET": "#0284c7",
                "POST": "#16a34a",
                "PUT": "#d97706",
                "PATCH": "#7c3aed",
                "DELETE": "#dc2626",
            }
            blocks_html = []
            for ev in api_evidences:
                m_color = method_colors.get(ev["method"], "#475569")
                req_json_str = (
                    json.dumps(ev["request_body"], indent=2, ensure_ascii=False)
                    if ev["request_body"] is not None
                    else "Sin cuerpo (No Payload)"
                )
                resp_body = ev["response_body"]
                if isinstance(resp_body, list) and len(resp_body) > 2:
                    preview = resp_body[:2] + [
                        f"... ({len(resp_body) - 2} elementos adicionales validados)"
                    ]
                    resp_json_str = json.dumps(preview, indent=2, ensure_ascii=False)
                else:
                    resp_json_str = json.dumps(resp_body, indent=2, ensure_ascii=False)

                blocks_html.append(
                    f"""
                    <div style="margin-top: 10px; padding: 12px; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">
                            <div>
                                <span style="background: {m_color}; color: white; padding: 3px 9px; border-radius: 4px; font-size: 11px; font-weight: 800;">{html.escape(ev['method'])}</span>
                                <code style="margin-left: 8px; font-size: 12px; color: #0f172a; font-weight: 600;">{html.escape(ev['url'])}</code>
                            </div>
                            <div style="font-size: 12px; color: #334155;">
                                <strong>Status:</strong> <span style="color: #059669; font-weight: 700;">{ev['status_code']}</span> (Esperado: {ev['expected_status']}) &nbsp;|&nbsp;
                                <strong>Tiempo:</strong> <span style="color: #0284c7; font-weight: 700;">{ev['elapsed_ms']} ms</span>
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px;">
                            <div>
                                <div style="font-size: 11px; font-weight: 700; color: #475569; margin-bottom: 4px;">📤 Request Payload:</div>
                                <pre style="margin: 0; background: #0f172a; color: #e2e8f0; padding: 10px; border-radius: 6px; font-size: 11px; overflow-x: auto; white-space: pre-wrap;">{html.escape(req_json_str)}</pre>
                            </div>
                            <div>
                                <div style="font-size: 11px; font-weight: 700; color: #475569; margin-bottom: 4px;">📥 Response JSON:</div>
                                <pre style="margin: 0; background: #0f172a; color: #a7f3d0; padding: 10px; border-radius: 6px; font-size: 11px; overflow-x: auto; white-space: pre-wrap;">{html.escape(resp_json_str)}</pre>
                            </div>
                        </div>
                    </div>
                    """
                )
            api_card_html = f"""
            <div style="margin: 12px 0; padding: 16px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 6px;">🔎 Evidencia de Peticiones y Respuestas HTTP (API REST)</div>
                {''.join(blocks_html)}
            </div>
            """
            extras.append(pytest_html.extras.html(api_card_html))

    report.extras = extras


def pytest_testnodedown(node, error):
    """Soporte opcional para pytest-xdist."""
    pass


@pytest.hookimpl(trylast=True)
def pytest_runtest_logreport(report):
    """Recopila resultados en el nodo controlador también durante ejecuciones paralelas (pytest-xdist)."""
    if report.when == "call" and os.environ.get("PYTEST_XDIST_WORKER") is None:
        # Si estamos en modo xdist (controller), _SESSION_RESULTS no fue llenado por makereport local
        test_cat = getattr(report, "test_category", None)
        if test_cat is None:
            test_cat = "api" if "test_api_" in report.nodeid else "ui"
        # Evitar duplicar si ya fue agregado en ejecución secuencial sin xdist
        if not any(r.get("nodeid") == report.nodeid for r in _SESSION_RESULTS):
            _SESSION_RESULTS.append(
                {
                    "nodeid": report.nodeid,
                    "passed": report.passed,
                    "failed": report.failed,
                    "skipped": report.skipped,
                    "type": test_cat,
                }
            )


def pytest_html_results_table_header(cells):
    """Inserta una columna descriptiva en el encabezado de la tabla de resultados."""
    cells.insert(2, '<th class="sortable" style="min-width: 260px;">Descripción del Caso</th>')


def pytest_html_results_table_row(report, cells):
    """Inserta la descripción correspondiente a cada caso de prueba en la tabla."""
    desc = getattr(report, "description", "")
    cells.insert(2, f'<td style="font-weight: 600; color: #1e293b;">{html.escape(desc)}</td>')


def pytest_html_results_summary(prefix, summary, postfix, session):
    """Añade un dashboard ejecutivo con estilos modernos, KPIs dinámicos y apertura automática de detalles."""
    # Deduplicar por nodeid en caso de que makereport y logreport hayan registrado el mismo ítem
    unique_results = []
    seen_nodes = set()
    for r in _SESSION_RESULTS:
        nid = r.get("nodeid")
        if nid:
            if nid in seen_nodes:
                continue
            seen_nodes.add(nid)
        unique_results.append(r)

    # Si tanto makereport (sin nodeid) como logreport (con nodeid) corrieron en modo secuencial,
    # priorizar los registros con nodeid para exactitud
    with_nodeid = [r for r in _SESSION_RESULTS if r.get("nodeid")]
    active_results = with_nodeid if with_nodeid else unique_results

    total_tests = len(active_results)
    passed_tests = sum(1 for r in active_results if r["passed"])
    failed_tests = sum(1 for r in active_results if r["failed"])
    ui_tests = sum(1 for r in active_results if r["type"] == "ui")
    api_tests = sum(1 for r in active_results if r["type"] == "api")
    pass_rate = round((passed_tests / total_tests) * 100) if total_tests > 0 else 100

    # Codificar README.md en Base64 para permitir su descarga directa desde el reporte HTML (local y GitHub Pages)
    readme_path = BASE_DIR / "README.md"
    try:
        readme_bytes = readme_path.read_bytes()
    except Exception:
        readme_bytes = b"# README.md no disponible"
    readme_b64 = base64.b64encode(readme_bytes).decode("ascii")

    # Marca de tiempo en Hora Universal Coordinada (UTC)
    utc_timestamp = datetime.now(timezone.utc).strftime("%d-%b-%Y at %H:%M:%S UTC")

    custom_assets = f"""
    <script>
        // Descarga directa y autocontenida del archivo README.md en UTF-8
        var _QA_README_B64 = "{readme_b64}";
        var _QA_UTC_TIMESTAMP = "{utc_timestamp}";
        function downloadQaReadme(evt) {{
            try {{
                if (evt && evt.preventDefault) {{
                    evt.preventDefault();
                }}
                var binStr = window.atob(_QA_README_B64);
                var bytes = new Uint8Array(binStr.length);
                for (var i = 0; i < binStr.length; i++) {{
                    bytes[i] = binStr.charCodeAt(i);
                }}
                var blob = new Blob([bytes], {{ type: "application/octet-stream" }});
                if (window.navigator && window.navigator.msSaveOrOpenBlob) {{
                    window.navigator.msSaveOrOpenBlob(blob, "README.md");
                    return false;
                }}
                var url = window.URL.createObjectURL(blob);
                var a = document.createElement("a");
                a.style.display = "none";
                a.href = url;
                a.setAttribute("download", "README.md");
                document.body.appendChild(a);
                a.click();
                setTimeout(function() {{
                    if (a.parentNode) {{
                        a.parentNode.removeChild(a);
                    }}
                    window.URL.revokeObjectURL(url);
                }}, 500);
                return false;
            }} catch (e) {{
                console.error("Error al descargar README.md vía Blob, usando fallback nativo:", e);
                return true;
            }}
        }}

        function ensureUtcIndicator() {{
            var paragraphs = document.getElementsByTagName("p");
            for (var i = 0; i < paragraphs.length; i++) {{
                var p = paragraphs[i];
                if (p.innerHTML && p.innerHTML.indexOf("Report generated on ") !== -1) {{
                    p.innerHTML = p.innerHTML.replace(
                        /Report generated on [0-9]{{2}}-[A-Za-z]{{3}}-[0-9]{{4}} at [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}}(?:\\s*UTC)?/,
                        "Report generated on " + _QA_UTC_TIMESTAMP
                    );
                    break;
                }}
            }}
        }}
        ensureUtcIndicator();

        // Monkey-patch seguro para prevenir Uncaught DOMException: pushState en URLs file:// locales
        (function() {{
            var origPush = window.history.pushState;
            var origReplace = window.history.replaceState;
            window.history.pushState = function(state, title, url) {{
                try {{
                    if (origPush) origPush.call(window.history, state, title, url);
                }} catch(e) {{
                    console.warn("pushState capturado y prevenido para origen file://:", e);
                }}
            }};
            window.history.replaceState = function(state, title, url) {{
                try {{
                    if (origReplace) origReplace.call(window.history, state, title, url);
                }} catch(e) {{
                    console.warn("replaceState capturado y prevenido para origen file://:", e);
                }}
            }};
        }})();

        // Limpiar caché de colapso y forzar apertura automática de todos los detalles visuales al cargar
        try {{
            sessionStorage.removeItem('collapsedIds');
            sessionStorage.removeItem('sortAsc');
        }} catch(e) {{}}

        window.addEventListener('DOMContentLoaded', function() {{
            ensureUtcIndicator();
            setTimeout(function() {{
                var btn = document.getElementById('show_all_details');
                if (btn) {{ btn.click(); }}
            }}, 50);
        }});
    </script>
    <style>
        /* Estilos modernos para un reporte ejecutivo */
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
            background-color: #f8fafc !important;
            color: #1e293b !important;
            padding: 24px 48px !important;
        }}
        #title {{
            font-size: 26px !important;
            font-weight: 800 !important;
            color: #0f172a !important;
            margin-bottom: 4px !important;
        }}
        /* Respetar el colapso/ocultamiento al hacer clic en Hide All Details */
        .extras-row.hidden {{
            display: none !important;
        }}
        /* Ampliar y centrar las capturas de pantalla de evidencia */
        div.media {{
            float: none !important;
            width: 100% !important;
            max-width: 950px !important;
            height: auto !important;
            margin: 20px auto !important;
            border-radius: 10px !important;
            border: 2px solid #cbd5e1 !important;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05) !important;
            background: #ffffff !important;
            padding: 8px !important;
            overflow: visible !important;
        }}
        .media-container {{
            height: auto !important;
            display: block !important;
        }}
        .media-container__viewport img {{
            max-height: 580px !important;
            width: auto !important;
            max-width: 100% !important;
            object-fit: contain !important;
            border-radius: 6px !important;
            display: block !important;
            margin: 0 auto !important;
        }}
        /* Estilo para los logs de ejecución */
        .logwrapper {{
            max-height: 300px !important;
            border-radius: 8px !important;
            background-color: #0f172a !important;
            border: 1px solid #1e293b !important;
            margin-top: 15px !important;
        }}
        .logwrapper .log {{
            color: #f1f5f9 !important;
            font-family: Consolas, 'Fira Code', monospace !important;
            font-size: 11px !important;
            line-height: 1.5 !important;
            padding: 12px 18px !important;
            background: transparent !important;
        }}
        /* Tabla de resultados */
        #results-table {{
            border-radius: 10px !important;
            overflow: hidden !important;
            border: 1px solid #e2e8f0 !important;
            background: #ffffff !important;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
            width: 100% !important;
            margin-top: 15px !important;
        }}
        #results-table th {{
            background-color: #f1f5f9 !important;
            color: #475569 !important;
            font-weight: 700 !important;
            padding: 12px 16px !important;
            border-bottom: 2px solid #e2e8f0 !important;
        }}
        #results-table td {{
            padding: 12px 16px !important;
            border-bottom: 1px solid #f1f5f9 !important;
        }}
        .col-result {{
            font-weight: bold !important;
        }}
        /* Botón de descarga de README.md con Tooltip interactivo */
        .qa-readme-tooltip-wrapper {{
            position: relative;
            display: inline-block;
            margin-top: 10px;
        }}
        .qa-readme-btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
            color: #ffffff !important;
            border: 1px solid rgba(125, 211, 252, 0.45);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(2, 132, 199, 0.35);
            transition: all 0.2s ease-in-out;
            text-decoration: none;
        }}
        .qa-readme-btn:hover {{
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
            transform: translateY(-1px);
            box-shadow: 0 6px 14px rgba(14, 165, 233, 0.5);
        }}
        .qa-readme-tooltip-text {{
            visibility: hidden;
            opacity: 0;
            width: 320px;
            background-color: #0f172a;
            color: #f8fafc;
            text-align: left;
            border: 1px solid #38bdf8;
            border-radius: 8px;
            padding: 10px 12px;
            position: absolute;
            z-index: 9999;
            top: 120%;
            right: 0;
            font-size: 12px;
            font-weight: 400;
            line-height: 1.45;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.45);
            transition: opacity 0.2s ease-in-out, visibility 0.2s ease-in-out;
            pointer-events: none;
        }}
        .qa-readme-tooltip-wrapper:hover .qa-readme-tooltip-text {{
            visibility: visible;
            opacity: 1;
        }}
    </style>

    <!-- Banner Ejecutivo con KPIs Dinámicos -->
    <div style="margin: 20px 0 25px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: white; padding: 24px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.2);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
                <div>
                    <h2 style="margin: 0 0 6px 0; color: #38bdf8; font-size: 20px; font-weight: 800;">🎓 Entrega Final de Proyecto: Framework de Automatización QA</h2>
                    <p style="margin: 0; color: #94a3b8; font-size: 13px;">Suite Integrada de Pruebas UI (SauceDemo con POM + CSV/JSON/Faker) y API REST (JSONPlaceholder con Requests Session + Pydantic)</p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 14px; color: #f8fafc;"><strong>Estudiante / Autor:</strong> Vincenzo Natale (vnatale52@gmail.com)</div>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Framework: Python + Pytest + Selenium WebDriver + Requests + Pydantic</div>
                    <div class="qa-readme-tooltip-wrapper">
                        <a href="data:application/octet-stream;base64,{readme_b64}" download="README.md" class="qa-readme-btn" onclick="return downloadQaReadme(event);" title="Haz clic para descargar la documentación técnica completa del proyecto (README.md): arquitectura POM, localizadores comentados, casos UI/API, pipelines CI/CD y las 7 mejoras avanzadas de Ingeniería QA.">
                            📥 Descargar README.md
                        </a>
                        <div class="qa-readme-tooltip-text">
                            <strong style="color: #38bdf8; display: block; margin-bottom: 4px;">📄 Documentación Técnica Completa (README.md)</strong>
                            Haz clic aquí para descargar el archivo <code>README.md</code> del proyecto con el propósito detallado, arquitectura POM, explicación de localizadores, cobertura de 22 pruebas (UI + API), pipelines CI/CD en GitHub Actions y las 7 mejoras avanzadas de Ingeniería QA.
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tarjetas de Métricas (KPIs) -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; margin-top: 20px;">
                <div style="background: rgba(255, 255, 255, 0.07); padding: 14px 18px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: 600;">Total Ejecutadas</div>
                    <div style="font-size: 24px; font-weight: 800; color: #ffffff; margin-top: 4px;">{total_tests}</div>
                </div>
                <div style="background: rgba(16, 185, 129, 0.15); padding: 14px 18px; border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.3);">
                    <div style="font-size: 11px; text-transform: uppercase; color: #6ee7b7; font-weight: 600;">Aprobadas (Passed)</div>
                    <div style="font-size: 24px; font-weight: 800; color: #34d399; margin-top: 4px;">{passed_tests} ({pass_rate}%)</div>
                </div>
                <div style="background: rgba(239, 68, 68, 0.1); padding: 14px 18px; border-radius: 8px; border: 1px solid rgba(239, 68, 68, 0.2);">
                    <div style="font-size: 11px; text-transform: uppercase; color: #fca5a5; font-weight: 600;">Fallidas (Failed)</div>
                    <div style="font-size: 24px; font-weight: 800; color: #f87171; margin-top: 4px;">{failed_tests}</div>
                </div>
                <div style="background: rgba(56, 189, 248, 0.12); padding: 14px 18px; border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.25);">
                    <div style="font-size: 11px; text-transform: uppercase; color: #7dd3fc; font-weight: 600;">Cobertura UI / API</div>
                    <div style="font-size: 15px; font-weight: 700; color: #38bdf8; margin-top: 8px;">{ui_tests} UI &nbsp;|&nbsp; {api_tests} API</div>
                </div>
            </div>
        </div>
    </div>
    """
    prefix.extend([custom_assets])


def pytest_html_report_title(report):
    """Personaliza el título de la pestaña y encabezado del reporte HTML."""
    report.title = "Reporte de Pruebas Automatizadas UI & API - Entrega Final QA (Vincenzo Natale)"


def pytest_unconfigure(config):
    """Post-procesa el reporte HTML generado para fijar la hora universal (UTC) en el encabezado y sincronizar index.html/README.md."""
    if os.environ.get("PYTEST_XDIST_WORKER") is not None:
        return
    report_path = BASE_DIR / "reports" / "reporte.html"
    if report_path.exists():
        try:
            content = report_path.read_text(encoding="utf-8")
            utc_now = datetime.now(timezone.utc).strftime("%d-%b-%Y at %H:%M:%S UTC")
            updated_content = re.sub(
                r"Report generated on \d{2}-[A-Za-z]{3}-\d{4} at \d{2}:\d{2}:\d{2}(?:\s*UTC)?",
                f"Report generated on {utc_now}",
                content,
                count=1,
            )
            report_path.write_text(updated_content, encoding="utf-8")
            index_path = BASE_DIR / "reports" / "index.html"
            shutil.copyfile(report_path, index_path)
            readme_src = BASE_DIR / "README.md"
            if readme_src.exists():
                shutil.copyfile(readme_src, BASE_DIR / "reports" / "README.md")
        except Exception as exc:
            logger.warning(f"No se pudo post-procesar reporte.html con hora UTC: {exc}")
