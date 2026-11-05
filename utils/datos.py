import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
from faker import Faker
from utils.config import DATOS_DIR

fake = Faker("es_ES")


def leer_csv_login(ruta_archivo: Path = DATOS_DIR / "login.csv") -> List[Tuple[str, str, bool, str, str]]:
    """Lee un archivo CSV de credenciales y devuelve una lista de tuplas para parametrización en Pytest."""
    datos = []
    ruta = Path(ruta_archivo)
    with open(ruta, mode="r", newline="", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            usuario = fila["usuario"].strip()
            clave = fila["clave"].strip()
            debe_funcionar = fila["debe_funcionar"].strip().lower() == "true"
            mensaje_esperado = fila["mensaje_esperado"].strip()
            descripcion = fila["descripcion"].strip()
            datos.append((usuario, clave, debe_funcionar, mensaje_esperado, descripcion))
    return datos


def leer_json_productos(ruta_archivo: Path = DATOS_DIR / "productos.json") -> List[Dict[str, Any]]:
    """Lee un archivo JSON con información de productos del catálogo para pruebas data-driven."""
    ruta = Path(ruta_archivo)
    with open(ruta, mode="r", encoding="utf-8") as archivo:
        return json.load(archivo)


def generar_datos_checkout_faker() -> Dict[str, str]:
    """Genera datos personales realistas y dinámicos con Faker para el formulario de Checkout."""
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "postal_code": fake.postcode(),
    }


def generar_post_api_faker(user_id: int = 1) -> Dict[str, Any]:
    """Genera un payload aleatorio pero realista con Faker para crear recursos vía API REST."""
    return {
        "title": f"QA Post Automatizado - {fake.sentence(nb_words=4).rstrip('.')}",
        "body": fake.paragraph(nb_sentences=2),
        "userId": user_id,
    }
