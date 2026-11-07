import pytest
from utils.api_utils import PostSchema, UserSchema, validate_api_response
from utils.config import API_BASE_URL
from utils.datos import generar_post_api_faker
from utils.logger import logger


@pytest.mark.api
@pytest.mark.smoke
def test_api_01_get_listar_usuarios(request, api_client):
    """Caso de Prueba API 01: Consultar lista de usuarios mediante método HTTP GET.

    Pasos:
    1. Enviar petición GET al endpoint '/users' de JSONPlaceholder usando sesión persistente (api_client).
    2. Verificar código de estado 200 OK, cabecera 'application/json' y tiempo de respuesta.
    3. Validar contrato JSON con Pydantic (UserSchema) y formato de datos de cada usuario.
    """
    logger.info("=== INICIO TEST API 01: GET /users ===")
    url = f"{API_BASE_URL}/users"
    response = api_client.get(url, timeout=10)

    users = validate_api_response(
        response=response,
        expected_status=200,
        schema_model=UserSchema,
        request_node=request.node,
        step_label="GET /users - Listar usuarios registrados (Contrato UserSchema)",
    )

    assert isinstance(users, list), "La respuesta de '/users' debe ser una lista JSON."
    assert len(users) > 0, "La lista de usuarios devuelta está vacía."

    required_keys = {"id", "name", "username", "email", "address", "company"}
    for user in users:
        assert required_keys <= set(user.keys()), (
            f"El usuario con ID {user.get('id')} no contiene todas las claves esperadas: {required_keys}"
        )
        assert "@" in user["email"], f"El email '{user['email']}' no tiene un formato válido."

    logger.info(f"Total de usuarios validados exitosamente: {len(users)}")
    logger.info("=== TEST API 01 COMPLETADO CON ÉXITO ===")


@pytest.mark.api
@pytest.mark.negative
def test_api_02_get_recurso_inexistente_negativo(request, api_client):
    """Caso de Prueba API 02: Consultar un recurso inexistente mediante GET (Escenario Negativo 404).

    Pasos:
    1. Enviar petición GET al endpoint '/posts/999999' (ID inexistente) mediante api_client.
    2. Verificar que el servidor responda con código HTTP 404 Not Found.
    3. Comprobar que el cuerpo de la respuesta sea un objeto JSON vacío '{}'.
    """
    logger.info("=== INICIO TEST API 02: GET /posts/999999 (Escenario Negativo 404) ===")
    url = f"{API_BASE_URL}/posts/999999"
    response = api_client.get(url, timeout=10)

    body = validate_api_response(
        response=response,
        expected_status=404,
        request_node=request.node,
        step_label="GET /posts/999999 - Recurso inexistente (404 Not Found)",
    )

    assert body == {}, f"Se esperaba un objeto vacío '{{}}' para 404, pero se recibió: {body}"
    logger.info("=== TEST API 02 COMPLETADO CON ÉXITO ===")


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.parametrize(
    "payload",
    [
        {
            "title": "Automatización de Pruebas QA - Entrega Final",
            "body": "Validación de creación de recursos mediante petición HTTP POST con Requests.",
            "userId": 1,
        },
        {
            "title": "Reporte Ejecutivo y Trazabilidad en Pytest",
            "body": "Integración de pruebas de UI con Selenium y pruebas de API con JSONPlaceholder.",
            "userId": 2,
        },
    ],
    ids=["post_recurso_qa_1", "post_recurso_qa_2"],
)
def test_api_03_post_crear_recurso_parametrizado(request, api_client, payload):
    """Caso de Prueba API 03: Crear nuevos recursos mediante método HTTP POST (Parametrizado).

    Pasos:
    1. Enviar petición POST al endpoint '/posts' con payload JSON parametrizado mediante api_client.
    2. Verificar código de estado 201 Created, cabecera 'application/json' y contrato PostSchema.
    3. Validar que la respuesta incluya el 'id' entero generado y refleje exactamente 'title', 'body' y 'userId'.
    """
    logger.info(f"=== INICIO TEST API 03: POST /posts | Título='{payload['title']}' ===")
    url = f"{API_BASE_URL}/posts"
    response = api_client.post(url, json=payload, timeout=10)

    created = validate_api_response(
        response=response,
        expected_status=201,
        expected_fields={"id", "title", "body", "userId"},
        expected_types={"id": int, "title": str, "body": str, "userId": int},
        schema_model=PostSchema,
        request_node=request.node,
        step_label=f"POST /posts - Crear recurso ({payload['title']})",
    )

    assert created["id"] is not None and int(created["id"]) > 0
    assert created["title"] == payload["title"]
    assert created["body"] == payload["body"]
    assert created["userId"] == payload["userId"]
    logger.info(f"Recurso creado exitosamente con ID: {created['id']}")
    logger.info("=== TEST API 03 COMPLETADO CON ÉXITO ===")


@pytest.mark.api
@pytest.mark.regression
def test_api_04_put_reemplazar_recurso_completo(request, api_client, test_data):
    """Caso de Prueba API 04: Reemplazar completamente un recurso existente mediante método HTTP PUT.

    Pasos:
    1. Enviar petición PUT al endpoint '/posts/1' con todos los campos del recurso ('id', 'title', 'body', 'userId').
    2. Verificar código de estado 200 OK, tipos de datos y contrato PostSchema del JSON devuelto.
    3. Confirmar que los valores devueltos coincidan exactamente con el payload enviado.
    """
    logger.info("=== INICIO TEST API 04: PUT /posts/1 ===")
    url = f"{API_BASE_URL}/posts/1"
    payload = test_data["api_data"]["put_payload"]

    response = api_client.put(url, json=payload, timeout=10)
    updated = validate_api_response(
        response=response,
        expected_status=200,
        expected_fields={"id", "title", "body", "userId"},
        expected_types={"id": int, "title": str, "body": str, "userId": int},
        schema_model=PostSchema,
        request_node=request.node,
        step_label="PUT /posts/1 - Reemplazo total del recurso #1",
    )

    assert updated["id"] == payload["id"]
    assert updated["title"] == payload["title"]
    assert updated["body"] == payload["body"]
    assert updated["userId"] == payload["userId"]
    logger.info("=== TEST API 04 COMPLETADO CON ÉXITO ===")


@pytest.mark.api
@pytest.mark.regression
def test_api_05_patch_actualizar_recurso_parcial(request, api_client, test_data):
    """Caso de Prueba API 05: Actualizar parcialmente un recurso mediante método HTTP PATCH.

    Pasos:
    1. Enviar petición PATCH al endpoint '/posts/1' enviando únicamente el campo 'title'.
    2. Verificar código de estado 200 OK y contrato PostSchema.
    3. Validar que el campo 'title' se haya actualizado y que los demás campos ('id', 'body', 'userId') se preserven.
    """
    logger.info("=== INICIO TEST API 05: PATCH /posts/1 ===")
    url = f"{API_BASE_URL}/posts/1"
    patch_payload = test_data["api_data"]["patch_payload"]

    response = api_client.patch(url, json=patch_payload, timeout=10)
    patched = validate_api_response(
        response=response,
        expected_status=200,
        expected_fields={"id", "title", "body", "userId"},
        expected_types={"id": int, "title": str, "body": str, "userId": int},
        schema_model=PostSchema,
        request_node=request.node,
        step_label="PATCH /posts/1 - Actualización parcial de título",
    )

    assert patched["title"] == patch_payload["title"]
    assert patched["id"] == 1
    assert bool(patched["body"]), "El campo 'body' original debe preservarse tras un PATCH."
    logger.info("=== TEST API 05 COMPLETADO CON ÉXITO ===")


@pytest.mark.api
@pytest.mark.smoke
def test_api_06_delete_eliminar_recurso(request, api_client):
    """Caso de Prueba API 06: Eliminar un recurso existente mediante método HTTP DELETE.

    Pasos:
    1. Enviar petición DELETE al endpoint '/posts/1' mediante api_client.
    2. Verificar código de estado 200 OK y tiempo de respuesta óptimo.
    3. Confirmar que el cuerpo devuelto esté vacío ('{}').
    """
    logger.info("=== INICIO TEST API 06: DELETE /posts/1 ===")
    url = f"{API_BASE_URL}/posts/1"
    response = api_client.delete(url, timeout=10)

    deleted_body = validate_api_response(
        response=response,
        expected_status=200,
        request_node=request.node,
        step_label="DELETE /posts/1 - Eliminación del recurso #1",
    )

    assert deleted_body == {}, f"Se esperaba cuerpo vacío '{{}}' tras DELETE, pero se obtuvo: {deleted_body}"
    logger.info("=== TEST API 06 COMPLETADO CON ÉXITO ===")


@pytest.mark.api
@pytest.mark.e2e
@pytest.mark.smoke
def test_api_07_flujo_encadenado_crud_completo(request, api_client):
    """Caso de Prueba API 07: Encadenamiento de peticiones (Ciclo de vida CRUD: POST -> PATCH -> DELETE).

    Pasos:
    1. Crear un nuevo recurso en '/posts' con datos dinámicos generados por Faker (POST) y obtener su 'id'.
    2. Utilizar el 'id' obtenido para actualizar parcialmente su título mediante PATCH.
    3. Eliminar el recurso creado utilizando el mismo 'id' mediante DELETE y verificar su eliminación.
    """
    logger.info("=== INICIO TEST API 07: Flujo Encadenado CRUD (POST -> PATCH -> DELETE) ===")

    # Paso 1: Crear recurso (POST)
    post_payload = generar_post_api_faker(user_id=10)
    resp_create = api_client.post(f"{API_BASE_URL}/posts", json=post_payload, timeout=10)
    created_data = validate_api_response(
        response=resp_create,
        expected_status=201,
        expected_fields={"id", "title", "body", "userId"},
        expected_types={"id": int, "title": str, "body": str, "userId": int},
        schema_model=PostSchema,
        request_node=request.node,
        step_label="Paso 1 (POST): Crear recurso dinámico con Faker",
    )
    resource_id = created_data["id"]
    assert resource_id is not None

    # Paso 2: Actualizar recurso encadenado (PATCH)
    new_title = f"[ACTUALIZADO QA #{resource_id}] {post_payload['title']}"
    resp_patch = api_client.patch(
        f"{API_BASE_URL}/posts/{resource_id}",
        json={"title": new_title},
        timeout=10,
    )
    patched_data = validate_api_response(
        response=resp_patch,
        expected_status=200,
        expected_fields={"title"},
        expected_types={"title": str},
        request_node=request.node,
        step_label=f"Paso 2 (PATCH): Actualizar recurso encadenado ID={resource_id}",
    )
    assert patched_data["title"] == new_title

    # Paso 3: Eliminar recurso encadenado (DELETE)
    resp_delete = api_client.delete(f"{API_BASE_URL}/posts/{resource_id}", timeout=10)
    deleted_data = validate_api_response(
        response=resp_delete,
        expected_status=200,
        request_node=request.node,
        step_label=f"Paso 3 (DELETE): Eliminar recurso encadenado ID={resource_id}",
    )
    assert deleted_data == {}
    logger.info("=== TEST API 07 (ENCADENAMIENTO CRUD) COMPLETADO CON ÉXITO ===")
