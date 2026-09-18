from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from utils.config import CART_URL
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class CartPage(BasePage):
    """Page Object para la página del Carrito de Compras de SauceDemo."""

    # Localizadores de la página del carrito
    PAGE_TITLE = (By.CLASS_NAME, "title")
    CART_ITEMS = (By.CLASS_NAME, "cart_item")
    ITEM_QUANTITY = (By.CLASS_NAME, "cart_quantity")
    ITEM_NAME = (By.CLASS_NAME, "inventory_item_name")
    ITEM_PRICE = (By.CLASS_NAME, "inventory_item_price")
    REMOVE_BTN = (By.CSS_SELECTOR, "button.cart_button")
    CONTINUE_SHOPPING_BTN = (By.ID, "continue-shopping")
    CHECKOUT_BTN = (By.ID, "checkout")

    def __init__(self, driver):
        super().__init__(driver)
        self.url = CART_URL

    def wait_for_cart_loaded(self) -> "CartPage":
        """Espera a que la página del carrito esté completamente cargada."""
        self.wait_for_url_contains("/cart.html")
        self.find_element(self.PAGE_TITLE)
        return self

    def get_page_title(self) -> str:
        """Retorna el título de la página del carrito ('Your Cart')."""
        return self.get_text(self.PAGE_TITLE)

    def get_cart_items(self) -> List:
        """Retorna la lista de WebElements correspondientes a los ítems en el carrito."""
        return self.find_elements(self.CART_ITEMS)

    def get_cart_items_count(self) -> int:
        """Retorna la cantidad de ítems presentes en el carrito."""
        return len(self.get_cart_items())

    def get_cart_items_details(self) -> List[Dict[str, str]]:
        """Extrae la información detallada (nombre, precio, cantidad) de todos los productos en el carrito."""
        items = self.get_cart_items()
        details = []
        for item in items:
            name = item.find_element(*self.ITEM_NAME).text.strip()
            price = item.find_element(*self.ITEM_PRICE).text.strip()
            quantity = item.find_element(*self.ITEM_QUANTITY).text.strip()
            details.append({"name": name, "price": price, "quantity": quantity})
        logger.info(f"Detalles de productos en el carrito: {details}")
        return details

    def is_product_in_cart(self, product_name: str) -> bool:
        """Verifica si un producto con un nombre específico existe en el carrito."""
        items = self.get_cart_items_details()
        matching = any(item["name"] == product_name for item in items)
        logger.info(f"¿Producto '{product_name}' está en el carrito?: {matching}")
        return matching

    def is_checkout_button_visible(self) -> bool:
        """Verifica si el botón de Checkout está disponible."""
        return self.is_visible(self.CHECKOUT_BTN)
