from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from utils.config import INVENTORY_URL
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class InventoryPage(BasePage):
    """Page Object para la página del Catálogo / Inventario de SauceDemo."""

    # Localizadores de la cabecera y navegación
    PAGE_TITLE = (By.CLASS_NAME, "title")
    APP_LOGO = (By.CLASS_NAME, "app_logo")
    BURGER_MENU_BTN = (By.ID, "react-burger-menu-btn")
    SORT_DROPDOWN = (By.CLASS_NAME, "product_sort_container")
    CART_LINK = (By.CLASS_NAME, "shopping_cart_link")
    CART_BADGE = (By.CLASS_NAME, "shopping_cart_badge")

    # Localizadores de elementos del catálogo
    INVENTORY_ITEMS = (By.CLASS_NAME, "inventory_item")
    ITEM_NAME = (By.CLASS_NAME, "inventory_item_name")
    ITEM_PRICE = (By.CLASS_NAME, "inventory_item_price")
    ITEM_DESC = (By.CLASS_NAME, "inventory_item_desc")
    ADD_TO_CART_BTN = (By.CSS_SELECTOR, "button.btn_inventory")

    def __init__(self, driver):
        super().__init__(driver)
        self.url = INVENTORY_URL

    def wait_for_inventory_loaded(self) -> "InventoryPage":
        """Espera explícitamente a que la página de inventario cargue tras el login."""
        self.wait_for_url_contains("/inventory.html")
        self.find_element(self.PAGE_TITLE)
        self.find_element(self.APP_LOGO)
        self.find_element(self.INVENTORY_ITEMS)
        return self

    def get_page_header_title(self) -> str:
        """Retorna el título de la sección de productos ('Products')."""
        return self.get_text(self.PAGE_TITLE)

    def get_app_logo_title(self) -> str:
        """Retorna el título de la aplicación en el header ('Swag Labs')."""
        return self.get_text(self.APP_LOGO)

    def get_inventory_items(self) -> List:
        """Retorna la lista de WebElements correspondientes a los productos del inventario."""
        return self.find_elements(self.INVENTORY_ITEMS)

    def get_inventory_count(self) -> int:
        """Retorna la cantidad total de productos visibles en la página."""
        return len(self.get_inventory_items())

    def get_first_product_details(self) -> Dict[str, str]:
        """Extrae el nombre y precio del primer producto listado en el catálogo."""
        items = self.get_inventory_items()
        if not items:
            raise RuntimeError("No se encontraron productos visibles en el catálogo de inventario.")

        first_item = items[0]
        name = first_item.find_element(*self.ITEM_NAME).text.strip()
        price = first_item.find_element(*self.ITEM_PRICE).text.strip()
        logger.info(f"Primer producto detectado: Nombre='{name}', Precio='{price}'")
        return {"name": name, "price": price}

    def add_first_product_to_cart(self) -> Dict[str, str]:
        """Agrega el primer producto disponible al carrito y retorna sus datos."""
        items = self.find_elements(self.INVENTORY_ITEMS)
        if not items:
            raise RuntimeError("No hay productos disponibles para agregar al carrito.")

        first_item = items[0]
        name = first_item.find_element(*self.ITEM_NAME).text.strip()
        price = first_item.find_element(*self.ITEM_PRICE).text.strip()
        add_btn = first_item.find_element(*self.ADD_TO_CART_BTN)

        logger.info(f"Haciendo click en 'Add to cart' para el producto: {name}")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_btn)
        try:
            add_btn.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", add_btn)

        return {"name": name, "price": price}

    def get_cart_badge_count(self) -> int:
        """Obtiene el número mostrado en el badge del carrito. Retorna 0 si no está presente."""
        badges = self.driver.find_elements(*self.CART_BADGE)
        if not badges:
            return 0
        try:
            return int(badges[0].text.strip())
        except (ValueError, Exception):
            return 0

    def wait_for_cart_badge_count(self, expected_count: int, timeout: int = 5) -> int:
        """Espera explícitamente a que el badge del carrito alcance un valor específico."""
        from selenium.webdriver.support.ui import WebDriverWait
        WebDriverWait(self.driver, timeout).until(
            lambda d: self.get_cart_badge_count() == expected_count
        )
        return self.get_cart_badge_count()

    def is_menu_button_present(self) -> bool:
        """Valida que el botón de menú hamburguesa esté presente y visible."""
        return self.is_visible(self.BURGER_MENU_BTN)

    def is_sort_dropdown_present(self) -> bool:
        """Valida que el dropdown de ordenamiento de productos esté presente y visible."""
        return self.is_visible(self.SORT_DROPDOWN)

    def is_cart_icon_present(self) -> bool:
        """Valida que el ícono del carrito esté presente y visible."""
        return self.is_visible(self.CART_LINK)

    def go_to_cart(self) -> None:
        """Navega al carrito de compras haciendo clic en el ícono del carrito."""
        logger.info("Navegando a la página del carrito de compras...")
        self.click(self.CART_LINK)
