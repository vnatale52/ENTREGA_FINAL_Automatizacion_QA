import json
import logging
from typing import Any, Dict, Optional, Set, Type
import requests
from utils.config import API_MAX_RESPONSE_TIME

try:
    from pydantic import BaseModel, Field
except ImportError:
    BaseModel = object  # Fallback seguro si Pydantic aún no está instalado
    Field = lambda *args, **kwargs: None

logger = logging.getLogger(__name__)


# ==============================================================================
# Modelos de Contrato JSON con Pydantic (Mejora 9.2: Pruebas de Contrato API)
# ==============================================================================
if BaseModel is not object:

    class GeoSchema(BaseModel):
        lat: str
        lng: str

    class AddressSchema(BaseModel):
        street: str
        suite: str
        city: str
        zipcode: str
        geo: GeoSchema

    class CompanySchema(BaseModel):
        name: str
        catchPhrase: str
        bs: str

    class UserSchema(BaseModel):
        id: int = Field(gt=0)
        name: str = Field(min_length=1)
        username: str = Field(min_length=1)
        email: str = Field(min_length=3)
        address: AddressSchema
        company: CompanySchema

    class PostSchema(BaseModel):
        id: int = Field(gt=0)
        title: str = Field(min_length=1)
        body: Optional[str] = None
        userId: Optional[int] = None

else:
    UserSchema = None
    PostSchema = None


def validate_api_response(
    response: requests.Response,
    expected_status: int,
    expected_fields: Optional[Set[str]] = None,
    expected_types: Optional[Dict[str, Type]] = None,
    schema_model: Optional[Any] = None,
    max_time: float = API_MAX_RESPONSE_TIME,
    request_node: Any = None,
    step_label: str = "",
) -> Any:
    """Valida una respuesta HTTP en 5 niveles de calidad (incluyendo Contrato JSON y Tipos):
    1. Código de estado HTTP (Status Code).
    2. Cabeceras HTTP (Content-Type JSON).
    3. Estructura y contrato del esquema JSON (claves requeridas, tipos de datos y modelo Pydantic).
    4. Contenido / payload deserializado.
    5. Tiempo de respuesta (rendimiento).
    """
    elapsed_sec = response.elapsed.total_seconds()
    elapsed_ms = round(elapsed_sec * 1000, 2)
    method = response.request.method if response.request else "HTTP"
    url = response.url

    logger.info(
        f"[{method}] {url} -> Status: {response.status_code} (Esperado: {expected_status}) | Tiempo: {elapsed_ms} ms"
    )

    # Registrar evidencia para el reporte HTML si se proporcionó request.node
    if request_node is not None:
        if not hasattr(request_node, "api_evidences"):
            request_node.api_evidences = []
        try:
            resp_body = response.json() if response.text else {}
        except Exception:
            resp_body = response.text

        req_body = None
        if response.request and response.request.body:
            try:
                raw_body = response.request.body
                if isinstance(raw_body, bytes):
                    raw_body = raw_body.decode("utf-8")
                req_body = json.loads(raw_body)
            except Exception:
                req_body = str(response.request.body)

        request_node.api_evidences.append(
            {
                "step": step_label or f"{method} {url}",
                "method": method,
                "url": url,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "elapsed_ms": elapsed_ms,
                "request_body": req_body,
                "response_body": resp_body,
            }
        )

    # Nivel 1: Código de estado HTTP
    assert response.status_code == expected_status, (
        f"Código de estado inesperado en {method} {url}: "
        f"se esperaba {expected_status}, pero se recibió {response.status_code}."
    )

    # Nivel 2: Cabeceras (Content-Type debe ser application/json salvo en 204 No Content)
    if expected_status != 204:
        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type.lower(), (
            f"Cabecera Content-Type inválida: se esperaba 'application/json', pero se recibió '{content_type}'."
        )

    # Nivel 3 y 4: Estructura, tipos de datos y contrato JSON (Pydantic / expected_types)
    parsed_json = response.json() if response.text else {}
    if expected_fields is not None and isinstance(parsed_json, dict):
        missing = expected_fields - set(parsed_json.keys())
        assert not missing, (
            f"Faltan campos obligatorios en la respuesta JSON de {url}: {missing}. "
            f"Campos recibidos: {list(parsed_json.keys())}"
        )

    if expected_types is not None and isinstance(parsed_json, dict):
        for field_name, expected_type in expected_types.items():
            if field_name in parsed_json and parsed_json[field_name] is not None:
                actual_val = parsed_json[field_name]
                assert isinstance(actual_val, expected_type), (
                    f"Violación de tipo de dato en '{field_name}' ({url}): "
                    f"se esperaba {expected_type.__name__}, pero se recibió {type(actual_val).__name__} ({actual_val!r})."
                )

    if schema_model is not None and BaseModel is not object:
        if isinstance(parsed_json, list):
            for idx, elem in enumerate(parsed_json):
                schema_model.model_validate(elem)
            logger.info(
                f"Contrato Pydantic '{schema_model.__name__}' validado en {len(parsed_json)} elementos."
            )
        elif isinstance(parsed_json, dict) and parsed_json:
            schema_model.model_validate(parsed_json)
            logger.info(f"Contrato Pydantic '{schema_model.__name__}' validado exitosamente.")

    # Nivel 5: Tiempo de respuesta (Performance)
    assert elapsed_sec < max_time, (
        f"Tiempo de respuesta excedido en {method} {url}: {elapsed_sec:.3f}s supera el límite de {max_time}s."
    )

    return parsed_json
