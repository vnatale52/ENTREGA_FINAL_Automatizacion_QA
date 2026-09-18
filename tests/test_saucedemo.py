import pytest
import logging
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from pages.cart_page import CartPage

logger = logging.getLogger(__name__)


@pytest.mark.smoke
@pytest.mark.login
def test_01_login_exitoso(driver, test_data):
    """Caso de Prueba 1: Automatización de Login (Obligatorio).

    Pasos:
    1. Navegar a la página de login de saucedemo.com.
    2. Ingresar credenciales válidas (usuario: 'standard_user', contraseña: 'secret_sauce').
    3. Hacer clic en el botón de login.

    Validaciones (Criterios mínimos):
    - Espera explícita y validación de redirección a '/inventory.html'.
    - Validación de presencia de 'Products' en el encabezado de inventario.
    - Validación del título de la aplicación 'Swag Labs'.
    """
    logger.info("=== INICIO TEST 01: Login Exitoso ===")
    user = test_data["valid_user"]
    expected = test_data["expected_data"]

    # Paso 1: Navegar a la página de Login
    login_page = LoginPage(driver)
    login_page.load()
    assert login_page.is_login_page_loaded(), "La página de inicio de sesión no cargó correctamente."

    # Paso 2 y 3: Ingresar credenciales válidas y hacer click en Login
    login_page.login(username=user["username"], password=user["password"])

    # Validación 1: Espera explícita y verificación de redirección a /inventory.html
    inventory_page = InventoryPage(driver)
    inventory_page.wait_for_inventory_loaded()
    assert expected["inventory_url_part"] in inventory_page.get_current_url(), (
        f"La URL actual '{inventory_page.get_current_url()}' no contiene '{expected['inventory_url_part']}'"
    )

    # Validación 2: Título de la sección del catálogo ('Products')
    page_header = inventory_page.get_page_header_title()
    assert page_header == expected["inventory_title"], (
        f"El título de la página '{page_header}' no coincide con el esperado '{expected['inventory_title']}'"
    )

    # Validación 3: Título del navegador / Logo de la aplicación ('Swag Labs')
    app_logo_title = inventory_page.get_app_logo_title()
    browser_title = inventory_page.get_title()
    assert app_logo_title == expected["browser_title"], (
        f"El logo de la aplicación '{app_logo_title}' no coincide con '{expected['browser_title']}'"
    )
    assert expected["browser_title"] in browser_title, (
        f"El título del navegador '{browser_title}' no contiene '{expected['browser_title']}'"
    )
    logger.info("=== TEST 01 COMPLETADO CON ÉXITO ===")


@pytest.mark.smoke
@pytest.mark.catalog
def test_02_navegacion_catalogo(driver, test_data):
    """Caso de Prueba 2: Navegación y verificación del catálogo (Obligatorio).

    Pasos:
    1. Iniciar sesión con usuario válido.
    2. Esperar carga completa de la página de inventario.

    Validaciones (Criterios mínimos):
    - Valida que el título de la página de inventario sea correcto ('Products').
    - Comprueba que existan productos visibles en la página (al menos uno).
    - Extrae y lista el nombre y precio del primer producto.
    - Valida que elementos importantes de la interfaz estén presentes (menú hamburguesa, filtros, carrito).
    """
    logger.info("=== INICIO TEST 02: Navegación y Verificación del Catálogo ===")
    user = test_data["valid_user"]
    expected = test_data["expected_data"]

    # Precondición: Autenticación exitosa
    login_page = LoginPage(driver).load()
    login_page.login(username=user["username"], password=user["password"])

    inventory_page = InventoryPage(driver).wait_for_inventory_loaded()

    # Validación 1: Título de la página de inventario
    header_title = inventory_page.get_page_header_title()
    assert header_title == expected["inventory_title"], (
        f"Título esperado '{expected['inventory_title']}', pero se obtuvo '{header_title}'"
    )

    # Validación 2: Comprobar que existan productos visibles (al menos 1)
    total_items = inventory_page.get_inventory_count()
    assert total_items > 0, "No se encontraron productos visibles en el catálogo de inventario."
    logger.info(f"Cantidad total de productos detectados en el catálogo: {total_items}")

    # Validación 3: Extraer y listar nombre y precio del primer producto
    first_product = inventory_page.get_first_product_details()
    assert bool(first_product["name"]), "El nombre del primer producto está vacío."
    assert bool(first_product["price"]), "El precio del primer producto está vacío."
    assert "$" in first_product["price"], f"El precio '{first_product['price']}' no contiene formato de moneda ($)."
    logger.info(f"Detalles validados del primer producto: {first_product}")

    # Validación 4: Comprobar elementos importantes de la interfaz
    assert inventory_page.is_menu_button_present(), "El botón del menú lateral (hamburguesa) no está presente."
    assert inventory_page.is_sort_dropdown_present(), "El selector de filtros/ordenamiento no está presente."
    assert inventory_page.is_cart_icon_present(), "El ícono del carrito de compras no está presente."
    logger.info("=== TEST 02 COMPLETADO CON ÉXITO ===")


@pytest.mark.smoke
@pytest.mark.cart
def test_03_agregar_producto_carrito(driver, test_data):
    """Caso de Prueba 3: Interacción con productos y carrito (Obligatorio).

    Pasos:
    1. Iniciar sesión con credenciales válidas.
    2. Identificar el primer producto del catálogo.
    3. Añadir el producto al carrito haciendo clic en el botón correspondiente.
    4. Validar que el contador del carrito se incremente a '1'.
    5. Navegar a la página del carrito de compras (/cart.html).
    6. Comprobar que el producto añadido aparezca correctamente con su nombre y detalles.

    Validaciones (Criterios mínimos):
    - Agrega primer producto.
    - Verifica incremento de contador a 1.
    - Verifica ítem y sus datos presentes en el carrito.
    """
    logger.info("=== INICIO TEST 03: Interacción con Productos y Carrito ===")
    user = test_data["valid_user"]
    expected = test_data["expected_data"]

    # Precondición: Autenticación
    login_page = LoginPage(driver).load()
    login_page.login(username=user["username"], password=user["password"])

    inventory_page = InventoryPage(driver).wait_for_inventory_loaded()

    # Paso 1 y 2: Verificar contador inicial y agregar primer producto
    initial_badge_count = inventory_page.get_cart_badge_count()
    assert initial_badge_count == 0, f"El contador inicial del carrito debería ser 0, pero es {initial_badge_count}."

    added_product = inventory_page.add_first_product_to_cart()
    logger.info(f"Producto seleccionado para agregar: {added_product}")

    # Paso 3: Verificar que el contador del carrito se incremente correctamente (debe ser 1)
    updated_badge_count = inventory_page.wait_for_cart_badge_count(1)
    assert updated_badge_count == 1, (
        f"El contador del carrito esperado tras agregar 1 producto es 1, pero se obtuvo {updated_badge_count}."
    )

    # Paso 4: Navegar al carrito de compras
    inventory_page.go_to_cart()

    cart_page = CartPage(driver).wait_for_cart_loaded()

    # Validación 1: Verificar URL y título de la página del carrito
    assert expected["cart_url_part"] in cart_page.get_current_url(), (
        f"La URL '{cart_page.get_current_url()}' no corresponde al carrito ('{expected['cart_url_part']}')."
    )
    assert cart_page.get_page_title() == expected["cart_title"], (
        f"El título del carrito '{cart_page.get_page_title()}' no coincide con '{expected['cart_title']}'."
    )

    # Validación 2: Verificar que el carrito contenga exactamente 1 ítem
    assert cart_page.get_cart_items_count() == 1, (
        f"Se esperaba 1 producto en el carrito, pero se encontraron {cart_page.get_cart_items_count()}."
    )

    # Validación 3: Comprobar que el producto agregado coincida en nombre y precio
    cart_items = cart_page.get_cart_items_details()
    cart_item = cart_items[0]
    assert cart_item["name"] == added_product["name"], (
        f"El nombre del producto en el carrito '{cart_item['name']}' no coincide con el agregado '{added_product['name']}'."
    )
    assert cart_item["price"] == added_product["price"], (
        f"El precio del producto en el carrito '{cart_item['price']}' no coincide con el agregado '{added_product['price']}'."
    )
    assert cart_item["quantity"] == "1", f"La cantidad esperada es '1', pero se obtuvo '{cart_item['quantity']}'."

    # Validación adicional: Botón de Checkout disponible
    assert cart_page.is_checkout_button_visible(), "El botón de Checkout debería estar visible en el carrito."
    logger.info("=== TEST 03 COMPLETADO CON ÉXITO ===")
