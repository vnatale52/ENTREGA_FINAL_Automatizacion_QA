from pathlib import Path

# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# URLs del sistema web bajo prueba (SauceDemo - UI)
BASE_URL = "https://www.saucedemo.com"
INVENTORY_URL = f"{BASE_URL}/inventory.html"
CART_URL = f"{BASE_URL}/cart.html"
CHECKOUT_STEP_ONE_URL = f"{BASE_URL}/checkout-step-one.html"
CHECKOUT_STEP_TWO_URL = f"{BASE_URL}/checkout-step-two.html"
CHECKOUT_COMPLETE_URL = f"{BASE_URL}/checkout-complete.html"

# URL base para las pruebas de API REST (JSONPlaceholder)
API_BASE_URL = "https://jsonplaceholder.typicode.com"

# Configuración de tiempos de espera explícitos y umbrales de rendimiento
DEFAULT_TIMEOUT = 10
API_MAX_RESPONSE_TIME = 3.0

# Rutas de datos, evidencias, reportes y logs
DATOS_DIR = BASE_DIR / "datos"
REPORTS_DIR = BASE_DIR / "reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "suite.log"

# Asegurar que existan los directorios requeridos
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
