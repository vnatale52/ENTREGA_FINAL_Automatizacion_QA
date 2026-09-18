import os
from pathlib import Path

# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# URLs del sistema bajo prueba (SauceDemo)
BASE_URL = "https://www.saucedemo.com"
INVENTORY_URL = f"{BASE_URL}/inventory.html"
CART_URL = f"{BASE_URL}/cart.html"

# Configuración de tiempos de espera explícitos
DEFAULT_TIMEOUT = 10

# Rutas de evidencias y reportes
REPORTS_DIR = BASE_DIR / "reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"

# Asegurar que existan los directorios requeridos
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
