import pytest
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from utils.datos import (
    generar_datos_checkout_faker,
    leer_csv_login,
    leer_json_productos,
)
from utils.logger import logger

# Cargar datos externos para parametrización (Data-Driven Testing)
_RAW_LOGIN_CSV = leer_csv_login()
_LOGIN_CSV_IDS = [
    "csv_usuario_estandar_valido",
    "csv_usuario_bloqueado_negativo",
    "csv_credenciales_invalidas_negativo",
    "csv_usuario_vacio_negativo",
    "csv_clave_vacia_negativo",
]
# Asignar dinámicamente el marcador @pytest.mark.negative a los escenarios negativos del CSV
CASOS_LOGIN_PARAMETRIZADOS = [
    pytest.param(
        fila[0],
        fila[1],
        fila[2],
        fila[3],
        fila[4],
        id=_LOGIN_CSV_IDS[i] if i < len(_LOGIN_CSV_IDS) else f"csv_caso_{i+1}",
        marks=() if fila[2] else (pytest.mark.negative,),
    )
    for i, fila in enumerate(_RAW_LOGIN_CSV)
]

PRODUCTOS_JSON = leer_json_productos()


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.login
def test_01_login_exitoso(driver, test_data):
    """Caso de Prueba UI 01: Inicio de sesión exitoso con credenciales válidas (Smoke).

    Pasos:
    1. Navegar a la página de login de saucedemo.com.
    2. Ingresar credenciales válidas (usuario: 'standard_user', contraseña: 'secret_sauce').
    3. Hacer clic en el botón de login.

    Validaciones:
    - Espera explícita y redirección a '/inventory.html'.
    - Presencia de 'Products' en el encabezado de inventario.
    - Título de la aplicación 'Swag Labs'.
    """
    logger.info("=== INICIO TEST UI 01: Login Exitoso ===")
    user = test_data["valid_user"]
    expected = test_data["expected_data"]

    login_page = LoginPage(driver).load()
    assert login_page.is_login_page_loaded(), "La página de inicio de sesión no cargó correctamente."

    login_page.login(username=user["username"], password=user["password"])

    inventory_page = InventoryPage(driver).wait_for_inventory_loaded()
    assert expected["inventory_url_part"] in inventory_page.get_current_url(), (
        f"La URL actual '{inventory_page.get_current_url()}' no contiene '{expected['inventory_url_part']}'"
    )

    page_header = inventory_page.get_page_header_title()
    assert page_header == expected["inventory_title"], (
        f"El título de la página '{page_header}' no coincide con el esperado '{expected['inventory_title']}'"
    )

    app_logo_title = inventory_page.get_app_logo_title()
    browser_title = inventory_page.get_title()
    assert app_logo_title == expected["browser_title"], (
        f"El logo de la aplicación '{app_logo_title}' no coincide con '{expected['browser_title']}'"
    )
    assert expected["browser_title"] in browser_title, (
        f"El título del navegador '{browser_title}' no contiene '{expected['browser_title']}'"
    )
    logger.info("=== TEST UI 01 COMPLETADO CON ÉXITO ===")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.login
@pytest.mark.parametrize(
    "usuario, clave, debe_funcionar, mensaje_esperado, descripcion",
    CASOS_LOGIN_PARAMETRIZADOS,
)
def test_02_login_parametrizado_csv(
    driver, usuario, clave, debe_funcionar, mensaje_esperado, descripcion
):
    """Caso de Prueba UI 02: Login parametrizado desde archivo CSV externo (Positivos y Negativos).

    Pasos:
    1. Leer fila de datos desde 'datos/login.csv' mediante @pytest.mark.parametrize.
    2. Ingresar el usuario y contraseña correspondientes en la página de login.
    3. Validar redirección al inventario si 'debe_funcionar' es True, o verificar el mensaje de error exacto si es False.
    """
    logger.info(f"=== INICIO TEST UI 02 (CSV): {descripcion} | Usuario='{usuario}' ===")
    login_page = LoginPage(driver).load()
    login_page.login(username=usuario, password=clave)

    if debe_funcionar:
        inventory_page = InventoryPage(driver).wait_for_inventory_loaded()
        assert "/inventory.html" in inventory_page.get_current_url(), (
            "El inicio de sesión válido no redirigió al catálogo de inventario."
        )
        assert inventory_page.get_page_header_title() == "Products"
    else:
        assert login_page.is_error_displayed(), (
            f"Se esperaba un mensaje de error visible para el caso negativo: {descripcion}"
        )
        error_actual = login_page.get_error_message()
        assert mensaje_esperado in error_actual, (
            f"El mensaje de error '{error_actual}' no contiene el texto esperado '{mensaje_esperado}'."
        )
    logger.info(f"=== TEST UI 02 (CSV) COMPLETADO: {descripcion} ===")


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.catalog
def test_03_navegacion_y_filtro_catalogo(authenticated_inventory_page, test_data):
    """Caso de Prueba UI 03: Navegación del catálogo y ordenamiento de productos por precio.

    Pasos:
    1. Obtener sesión pre-autenticada en el catálogo mediante fixture 'authenticated_inventory_page' (DRY).
    2. Validar presencia de productos, menú hamburguesa, selector de ordenamiento e ícono de carrito.
    3. Extraer nombre y precio del primer producto.
    4. Ordenar los productos por precio de menor a mayor ('lohi') y verificar el orden numérico ascendente.
    5. Ordenar los productos por precio de mayor a menor ('hilo') y verificar el orden numérico descendente.
    """
    logger.info("=== INICIO TEST UI 03: Navegación y Filtro del Catálogo ===")
    expected = test_data["expected_data"]
    inventory_page = authenticated_inventory_page

    assert inventory_page.get_page_header_title() == expected["inventory_title"]
    total_items = inventory_page.get_inventory_count()
    assert total_items > 0, "No se encontraron productos visibles en el catálogo."

    first_product = inventory_page.get_first_product_details()
    assert bool(first_product["name"]) and "$" in first_product["price"]

    assert inventory_page.is_menu_button_present(), "El botón de menú lateral no está presente."
    assert inventory_page.is_sort_dropdown_present(), "El selector de filtros no está presente."
    assert inventory_page.is_cart_icon_present(), "El ícono del carrito no está presente."

    # Validar filtro de precio: menor a mayor (Price low to high)
    inventory_page.sort_products_by("lohi")
    prices_asc = inventory_page.get_all_product_prices()
    assert prices_asc == sorted(prices_asc), (
        f"Los precios no quedaron ordenados de menor a mayor: {prices_asc}"
    )

    # Validar filtro de precio: mayor a menor (Price high to low)
    inventory_page.sort_products_by("hilo")
    prices_desc = inventory_page.get_all_product_prices()
    assert prices_desc == sorted(prices_desc, reverse=True), (
        f"Los precios no quedaron ordenados de mayor a menor: {prices_desc}"
    )
    logger.info("=== TEST UI 03 COMPLETADO CON ÉXITO ===")


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.cart
def test_04_agregar_producto_carrito(driver, authenticated_inventory_page, test_data):
    """Caso de Prueba UI 04: Añadir el primer producto al carrito y verificar sus datos.

    Pasos:
    1. Obtener sesión pre-autenticada en el catálogo mediante fixture 'authenticated_inventory_page'.
    2. Añadir el primer producto del catálogo al carrito.
    3. Validar que el contador del carrito se incremente a '1'.
    4. Navegar al carrito (/cart.html) y verificar nombre, precio y cantidad ('1').
    """
    logger.info("=== INICIO TEST UI 04: Agregar Primer Producto al Carrito ===")
    expected = test_data["expected_data"]
    inventory_page = authenticated_inventory_page

    assert inventory_page.get_cart_badge_count() == 0
    added_product = inventory_page.add_first_product_to_cart()
    assert inventory_page.wait_for_cart_badge_count(1) == 1

    inventory_page.go_to_cart()
    cart_page = CartPage(driver).wait_for_cart_loaded()

    assert expected["cart_url_part"] in cart_page.get_current_url()
    assert cart_page.get_page_title() == expected["cart_title"]
    assert cart_page.get_cart_items_count() == 1

    cart_item = cart_page.get_cart_items_details()[0]
    assert cart_item["name"] == added_product["name"]
    assert cart_item["price"] == added_product["price"]
    assert cart_item["quantity"] == "1"
    assert cart_page.is_checkout_button_visible()
    logger.info("=== TEST UI 04 COMPLETADO CON ÉXITO ===")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.cart
@pytest.mark.parametrize(
    "producto",
    PRODUCTOS_JSON,
    ids=[p["nombre"].lower().replace(" ", "_") for p in PRODUCTOS_JSON],
)
def test_05_carrito_parametrizado_json(driver, authenticated_inventory_page, producto):
    """Caso de Prueba UI 05: Agregar productos al carrito parametrizados desde archivo JSON externo.

    Pasos:
    1. Leer cada objeto de producto desde 'datos/productos.json'.
    2. Obtener sesión pre-autenticada, buscar el producto por nombre exacto en el catálogo y agregarlo al carrito.
    3. Navegar al carrito y comprobar que el nombre y precio coincidan con los del archivo JSON.
    """
    nombre_esperado = producto["nombre"]
    precio_esperado = producto["precio"]
    logger.info(f"=== INICIO TEST UI 05 (JSON): Producto='{nombre_esperado}' ({precio_esperado}) ===")

    inventory_page = authenticated_inventory_page

    added_info = inventory_page.add_product_by_name(nombre_esperado)
    assert added_info["price"] == precio_esperado, (
        f"El precio en catálogo '{added_info['price']}' no coincide con el JSON '{precio_esperado}'."
    )
    assert inventory_page.wait_for_cart_badge_count(1) == 1

    inventory_page.go_to_cart()
    cart_page = CartPage(driver).wait_for_cart_loaded()
    assert cart_page.is_product_in_cart(nombre_esperado), (
        f"El producto '{nombre_esperado}' no se encontró dentro del carrito."
    )
    cart_item = cart_page.get_cart_items_details()[0]
    assert cart_item["price"] == precio_esperado
    logger.info(f"=== TEST UI 05 (JSON) COMPLETADO: '{nombre_esperado}' ===")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.cart
def test_06_eliminar_producto_carrito(driver, authenticated_inventory_page):
    """Caso de Prueba UI 06: Eliminar un producto del carrito de compras y verificar vaciado.

    Pasos:
    1. Obtener sesión pre-autenticada y añadir un producto al carrito.
    2. Navegar a la página del carrito y verificar que contiene 1 producto.
    3. Hacer clic en el botón 'Remove' del producto.
    4. Validar que el carrito quede vacío (0 productos) y sin contador activo.
    """
    logger.info("=== INICIO TEST UI 06: Eliminar Producto del Carrito ===")
    inventory_page = authenticated_inventory_page

    added = inventory_page.add_first_product_to_cart()
    assert inventory_page.wait_for_cart_badge_count(1) == 1

    inventory_page.go_to_cart()
    cart_page = CartPage(driver).wait_for_cart_loaded()
    assert cart_page.get_cart_items_count() == 1

    cart_page.remove_product_by_name(added["name"])
    assert cart_page.get_cart_items_count() == 0, (
        "El carrito debería quedar vacío (0 ítems) tras eliminar el producto."
    )
    logger.info("=== TEST UI 06 COMPLETADO CON ÉXITO ===")


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.e2e
@pytest.mark.checkout
def test_07_flujo_completo_checkout_e2e(driver, authenticated_inventory_page, test_data):
    """Caso de Prueba UI 07: Flujo End-to-End completo de compra y Checkout con datos Faker.

    Pasos:
    1. Obtener sesión pre-autenticada en el catálogo.
    2. Añadir el producto 'Sauce Labs Backpack' al carrito y navegar a '/cart.html'.
    3. Iniciar el proceso de Checkout y completar los datos de envío generados dinámicamente con Faker.
    4. Avanzar al resumen de compra ('Checkout: Overview') y validar presencia de subtotal y total.
    5. Confirmar la compra ('Finish') y verificar el mensaje 'Thank you for your order!'.
    """
    logger.info("=== INICIO TEST UI 07: Flujo Completo de Compra E2E (Checkout) ===")
    expected = test_data["expected_data"]
    datos_comprador = generar_datos_checkout_faker()
    inventory_page = authenticated_inventory_page

    added_product = inventory_page.add_product_by_name("Sauce Labs Backpack")
    assert inventory_page.wait_for_cart_badge_count(1) == 1

    inventory_page.go_to_cart()
    cart_page = CartPage(driver).wait_for_cart_loaded()
    assert cart_page.is_product_in_cart(added_product["name"])
    cart_page.click_checkout()

    checkout_page = CheckoutPage(driver).wait_for_step_one_loaded()
    assert checkout_page.get_page_title() == expected["checkout_step_one_title"]

    checkout_page.fill_customer_info(
        first_name=datos_comprador["first_name"],
        last_name=datos_comprador["last_name"],
        postal_code=datos_comprador["postal_code"],
    )
    checkout_page.click_continue()

    checkout_page.wait_for_step_two_loaded()
    assert checkout_page.get_page_title() == expected["checkout_step_two_title"]
    assert "Item total:" in checkout_page.get_subtotal_text()
    assert "Total:" in checkout_page.get_total_text()

    checkout_page.click_finish()
    checkout_page.wait_for_checkout_complete()
    assert checkout_page.get_page_title() == expected["checkout_complete_title"]
    assert checkout_page.get_complete_header() == expected["order_complete_header"]
    logger.info("=== TEST UI 07 COMPLETADO CON ÉXITO ===")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.checkout
def test_08_checkout_campos_obligatorios_negativo(driver, authenticated_inventory_page, test_data):
    """Caso de Prueba UI 08: Validación de campos obligatorios vacíos en Checkout (Escenario Negativo).

    Pasos:
    1. Obtener sesión pre-autenticada, agregar un producto al carrito e ingresar al Paso 1 del Checkout.
    2. Hacer clic en 'Continue' dejando vacíos los campos obligatorios (First Name, Last Name, Postal Code).
    3. Verificar que se muestre el mensaje de error 'Error: First Name is required'.
    """
    logger.info("=== INICIO TEST UI 08: Validación Negativa de Campos en Checkout ===")
    expected = test_data["expected_data"]
    inventory_page = authenticated_inventory_page

    inventory_page.add_first_product_to_cart()
    inventory_page.go_to_cart()

    cart_page = CartPage(driver).wait_for_cart_loaded()
    cart_page.click_checkout()

    checkout_page = CheckoutPage(driver).wait_for_step_one_loaded()
    checkout_page.click_continue()

    assert checkout_page.is_error_displayed(), (
        "Se esperaba un mensaje de error al intentar avanzar en Checkout sin datos del comprador."
    )
    assert expected["checkout_empty_first_name_error"] in checkout_page.get_error_message()
    logger.info("=== TEST UI 08 COMPLETADO CON ÉXITO ===")
