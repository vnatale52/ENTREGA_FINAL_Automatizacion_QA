import base64
import html
import json
import logging
import os
import sys
from datetime import datetime
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from utils.config import BASE_DIR, SCREENSHOTS_DIR
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


def pytest_addoption(parser):
    """Permite configurar parámetros de ejecución desde la línea de comandos."""
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Ejecutar el navegador Chrome en modo headless (sin interfaz gráfica).",
    )


@pytest.fixture(scope="session")
def test_data():
    """Carga los datos de prueba desde el archivo JSON centralizado."""
    data_path = BASE_DIR / "datos" / "test_data.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="function")
def driver(request):
    """Inicializa y destruye la instancia de WebDriver para cada prueba de interfaz (UI).

    Garantiza la total independencia entre casos de prueba (Teardown limpio).
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

    logger.info("Iniciando instancia de Chrome WebDriver para prueba UI...")
    browser = webdriver.Chrome(options=options)
    browser.maximize_window()

    # Inyección para que el hook de screenshot acceda al driver
    request.node.driver = browser

    yield browser

    logger.info("Cerrando sesión de WebDriver (Teardown)...")
    browser.quit()


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
        _SESSION_RESULTS.append(
            {
                "passed": report.passed,
                "failed": report.failed,
                "skipped": report.skipped,
                "type": "api" if is_api_test else "ui",
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


def pytest_html_results_table_header(cells):
    """Inserta una columna descriptiva en el encabezado de la tabla de resultados."""
    cells.insert(2, '<th class="sortable" style="min-width: 260px;">Descripción del Caso</th>')


def pytest_html_results_table_row(report, cells):
    """Inserta la descripción correspondiente a cada caso de prueba en la tabla."""
    desc = getattr(report, "description", "")
    cells.insert(2, f'<td style="font-weight: 600; color: #1e293b;">{html.escape(desc)}</td>')


def pytest_html_results_summary(prefix, summary, postfix, session):
    """Añade un dashboard ejecutivo con estilos modernos, KPIs dinámicos y apertura automática de detalles."""
    total_tests = len(_SESSION_RESULTS)
    passed_tests = sum(1 for r in _SESSION_RESULTS if r["passed"])
    failed_tests = sum(1 for r in _SESSION_RESULTS if r["failed"])
    ui_tests = sum(1 for r in _SESSION_RESULTS if r["type"] == "ui")
    api_tests = sum(1 for r in _SESSION_RESULTS if r["type"] == "api")
    pass_rate = round((passed_tests / total_tests) * 100) if total_tests > 0 else 100

    custom_assets = f"""
    <script>
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
    </style>

    <!-- Banner Ejecutivo con KPIs Dinámicos -->
    <div style="margin: 20px 0 25px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: white; padding: 24px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.2);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
                <div>
                    <h2 style="margin: 0 0 6px 0; color: #38bdf8; font-size: 20px; font-weight: 800;">🎓 Entrega Final de Proyecto: Framework de Automatización QA</h2>
                    <p style="margin: 0; color: #94a3b8; font-size: 13px;">Suite Integrada de Pruebas UI (SauceDemo con POM + CSV/JSON/Faker) y API REST (JSONPlaceholder con Requests)</p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 14px; color: #f8fafc;"><strong>Estudiante / Autor:</strong> Vincenzo Natale</div>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Framework: Python 3.13 + Pytest + Selenium WebDriver + Requests</div>
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
