from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from utils.config import (
    CHECKOUT_COMPLETE_URL,
    CHECKOUT_STEP_ONE_URL,
    CHECKOUT_STEP_TWO_URL,
)
import logging

logger = logging.getLogger(__name__)


class CheckoutPage(BasePage):
    """Page Object para el flujo completo de Checkout en SauceDemo (Pasos 1, 2 y Confirmación)."""

    # =========================================================================
    # Localizador general de cabecera en las 3 etapas de Checkout
    # =========================================================================
    PAGE_TITLE = (By.CLASS_NAME, "title")

    # =========================================================================
    # Localizadores Paso 1: Datos del comprador (/checkout-step-one.html)
    # =========================================================================
    # Campo de texto obligatorio para el nombre (atributo id='first-name')
    FIRST_NAME_INPUT = (By.ID, "first-name")
    # Campo de texto obligatorio para el apellido (atributo id='last-name')
    LAST_NAME_INPUT = (By.ID, "last-name")
    # Campo de texto obligatorio para el código postal (atributo id='postal-code')
    POSTAL_CODE_INPUT = (By.ID, "postal-code")
    # Botón para validar el formulario y avanzar al resumen (atributo id='continue')
    CONTINUE_BTN = (By.ID, "continue")
    # Botón para cancelar y volver al carrito (atributo id='cancel')
    CANCEL_BTN = (By.ID, "cancel")
    # Alerta de validación cuando algún campo obligatorio está vacío (data-test='error')
    ERROR_MESSAGE = (By.CSS_SELECTOR, "[data-test='error']")

    # =========================================================================
    # Localizadores Paso 2: Resumen financiero y confirmación (/checkout-step-two.html)
    # =========================================================================
    # Etiqueta con el subtotal de ítems antes de impuestos ('summary_subtotal_label')
    SUMMARY_SUBTOTAL = (By.CLASS_NAME, "summary_subtotal_label")
    # Etiqueta con el monto de impuestos calculados ('summary_tax_label')
    SUMMARY_TAX = (By.CLASS_NAME, "summary_tax_label")
    # Etiqueta con el monto total final a pagar ('summary_total_label')
    SUMMARY_TOTAL = (By.CLASS_NAME, "summary_total_label")
    # Botón final para confirmar y emitir la orden de compra (atributo id='finish')
    FINISH_BTN = (By.ID, "finish")

    # =========================================================================
    # Localizadores Paso 3: Orden completada (/checkout-complete.html)
    # =========================================================================
    # Encabezado principal de éxito ('Thank you for your order!', clase 'complete-header')
    COMPLETE_HEADER = (By.CLASS_NAME, "complete-header")
    # Párrafo descriptivo de confirmación de despacho ('complete-text')
    COMPLETE_TEXT = (By.CLASS_NAME, "complete-text")
    # Botón para volver al catálogo de productos tras finalizar la compra (id='back-to-products')
    BACK_HOME_BTN = (By.ID, "back-to-products")

    def __init__(self, driver):
        super().__init__(driver)
        self.step_one_url = CHECKOUT_STEP_ONE_URL
        self.step_two_url = CHECKOUT_STEP_TWO_URL
        self.complete_url = CHECKOUT_COMPLETE_URL

    def wait_for_step_one_loaded(self) -> "CheckoutPage":
        """Espera explícitamente la carga del Paso 1 del Checkout."""
        self.wait_for_url_contains("/checkout-step-one.html")
        self.find_element(self.FIRST_NAME_INPUT)
        return self

    def fill_customer_info(self, first_name: str, last_name: str, postal_code: str) -> "CheckoutPage":
        """Completa el formulario de datos de envío del comprador."""
        logger.info(
            f"Completando formulario de Checkout: Nombre='{first_name}', Apellido='{last_name}', CP='{postal_code}'"
        )
        self.type_text(self.FIRST_NAME_INPUT, first_name)
        self.type_text(self.LAST_NAME_INPUT, last_name)
        self.type_text(self.POSTAL_CODE_INPUT, postal_code)
        return self

    def click_continue(self) -> None:
        """Hace clic en el botón Continue para avanzar al resumen de la compra."""
        logger.info("Haciendo clic en 'Continue' en el formulario de Checkout...")
        self.click(self.CONTINUE_BTN)

    def is_error_displayed(self) -> bool:
        """Verifica si se muestra un mensaje de error en el formulario de Checkout."""
        return self.is_visible(self.ERROR_MESSAGE)

    def get_error_message(self) -> str:
        """Retorna el texto del mensaje de error en el formulario de Checkout."""
        return self.get_text(self.ERROR_MESSAGE)

    def wait_for_step_two_loaded(self) -> "CheckoutPage":
        """Espera explícitamente la carga del Paso 2 (Overview) del Checkout."""
        self.wait_for_url_contains("/checkout-step-two.html")
        self.find_element(self.SUMMARY_TOTAL)
        return self

    def get_page_title(self) -> str:
        """Obtiene el título de la sección actual de Checkout."""
        return self.get_text(self.PAGE_TITLE)

    def get_subtotal_text(self) -> str:
        """Obtiene el texto del subtotal antes de impuestos."""
        return self.get_text(self.SUMMARY_SUBTOTAL)

    def get_total_text(self) -> str:
        """Obtiene el texto del total final con impuestos incluidos."""
        return self.get_text(self.SUMMARY_TOTAL)

    def click_finish(self) -> None:
        """Hace clic en el botón Finish para confirmar y completar la orden."""
        logger.info("Confirmando orden de compra con el botón 'Finish'...")
        finish_btn = self.find_element(self.FINISH_BTN)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", finish_btn)
        try:
            finish_btn.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", finish_btn)

    def wait_for_checkout_complete(self) -> "CheckoutPage":
        """Espera explícitamente la pantalla de confirmación final de la compra."""
        self.wait_for_url_contains("/checkout-complete.html")
        self.find_element(self.COMPLETE_HEADER)
        return self

    def get_complete_header(self) -> str:
        """Obtiene el encabezado principal de confirmación ('Thank you for your order!')."""
        return self.get_text(self.COMPLETE_HEADER)

    def get_complete_text(self) -> str:
        """Obtiene el mensaje descriptivo de despacho de la orden."""
        return self.get_text(self.COMPLETE_TEXT)
