import json
import logging
from typing import Any, Dict, Optional, Set
import requests
from utils.config import API_MAX_RESPONSE_TIME

logger = logging.getLogger(__name__)


def validate_api_response(
    response: requests.Response,
    expected_status: int,
    expected_fields: Optional[Set[str]] = None,
    max_time: float = API_MAX_RESPONSE_TIME,
    request_node: Any = None,
    step_label: str = "",
) -> Any:
    """Valida una respuesta HTTP en 5 niveles de calidad:
    1. Código de estado HTTP (Status Code).
    2. Cabeceras HTTP (Content-Type JSON).
    3. Estructura del esquema JSON (claves requeridas).
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

    # Nivel 3 y 4: Estructura y contenido JSON
    parsed_json = response.json() if response.text else {}
    if expected_fields is not None and isinstance(parsed_json, dict):
        missing = expected_fields - set(parsed_json.keys())
        assert not missing, (
            f"Faltan campos obligatorios en la respuesta JSON de {url}: {missing}. "
            f"Campos recibidos: {list(parsed_json.keys())}"
        )

    # Nivel 5: Tiempo de respuesta (Performance)
    assert elapsed_sec < max_time, (
        f"Tiempo de respuesta excedido en {method} {url}: {elapsed_sec:.3f}s supera el límite de {max_time}s."
    )

    return parsed_json
