import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde archivo .env si existe (Mejora 9.6: Configuración Multi-Ambiente)
if load_dotenv is not None:
    load_dotenv(BASE_DIR / ".env")

# URLs del sistema web bajo prueba (SauceDemo - UI), configurables por variable de entorno
BASE_URL = os.getenv("BASE_URL_UI", "https://www.saucedemo.com").rstrip("/")
INVENTORY_URL = f"{BASE_URL}/inventory.html"
CART_URL = f"{BASE_URL}/cart.html"
CHECKOUT_STEP_ONE_URL = f"{BASE_URL}/checkout-step-one.html"
CHECKOUT_STEP_TWO_URL = f"{BASE_URL}/checkout-step-two.html"
CHECKOUT_COMPLETE_URL = f"{BASE_URL}/checkout-complete.html"

# URL base para las pruebas de API REST (JSONPlaceholder), configurable por variable de entorno
API_BASE_URL = os.getenv("BASE_URL_API", "https://jsonplaceholder.typicode.com").rstrip("/")

# Configuración de tiempos de espera explícitos, umbrales de rendimiento y visualización
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "10"))
API_MAX_RESPONSE_TIME = float(os.getenv("API_MAX_RESPONSE_TIME", "3.0"))
VISUAL_DELAY_SECONDS = float(os.getenv("VISUAL_DELAY_SECONDS", "5"))
DEFAULT_BROWSER = os.getenv("BROWSER", "chrome").lower()

# Rutas de datos, evidencias, reportes y logs
DATOS_DIR = BASE_DIR / "datos"
REPORTS_DIR = BASE_DIR / "reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "suite.log"

# Asegurar que existan los directorios requeridos
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
