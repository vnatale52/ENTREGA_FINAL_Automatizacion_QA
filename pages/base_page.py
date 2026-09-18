from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from typing import List, Tuple
from utils.config import DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)


class BasePage:
    """Clase base para todos los Page Objects.

    Proporciona métodos reutilizables con esperas explícitas (WebDriverWait)
    para interactuar de forma robusta con la interfaz web.
    """

    def __init__(self, driver: WebDriver, timeout: int = DEFAULT_TIMEOUT):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(self.driver, self.timeout)

    def open_url(self, url: str) -> None:
        """Navega a una URL específica."""
        logger.info(f"Navegando a: {url}")
        self.driver.get(url)

    def get_current_url(self) -> str:
        """Obtiene la URL actual del navegador."""
        return self.driver.current_url

    def get_title(self) -> str:
        """Obtiene el título de la pestaña actual."""
        return self.driver.title

    def find_element(self, locator: Tuple[str, str], timeout: int = None) -> WebElement:
        """Encuentra y espera a que un elemento esté visible en el DOM."""
        wait_time = timeout or self.timeout
        try:
            return WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located(locator)
            )
        except TimeoutException:
            logger.error(f"Elemento no visible tras {wait_time}s: {locator}")
            raise

    def find_elements(self, locator: Tuple[str, str], timeout: int = None) -> List[WebElement]:
        """Encuentra y espera la presencia de una lista de elementos en el DOM."""
        wait_time = timeout or self.timeout
        try:
            return WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_all_elements_located(locator)
            )
        except TimeoutException:
            logger.warning(f"No se encontraron elementos tras {wait_time}s: {locator}")
            return []

    def click(self, locator: Tuple[str, str], timeout: int = None) -> None:
        """Espera a que un elemento sea interactuable (clickable) y hace clic."""
        wait_time = timeout or self.timeout
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.element_to_be_clickable(locator)
            )
            element.click()
            logger.info(f"Click en elemento: {locator}")
        except TimeoutException:
            logger.error(f"Elemento no clickeable tras {wait_time}s: {locator}")
            raise

    def type_text(self, locator: Tuple[str, str], text: str, clear_first: bool = True, timeout: int = None) -> None:
        """Espera a que un campo esté visible, opcionalmente limpia y escribe el texto."""
        element = self.find_element(locator, timeout)
        if clear_first:
            element.clear()
        element.send_keys(text)
        logger.info(f"Texto ingresado en {locator}: '{text if 'pass' not in locator[1].lower() else '******'}'")

    def get_text(self, locator: Tuple[str, str], timeout: int = None) -> str:
        """Obtiene el texto visible de un elemento."""
        element = self.find_element(locator, timeout)
        text = element.text.strip()
        logger.info(f"Texto obtenido de {locator}: '{text}'")
        return text

    def is_visible(self, locator: Tuple[str, str], timeout: int = 5) -> bool:
        """Verifica si un elemento es visible en la página sin lanzar excepción."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except (TimeoutException, NoSuchElementException):
            return False

    def wait_for_url_contains(self, partial_url: str, timeout: int = None) -> bool:
        """Espera a que la URL contenga una subcadena específica."""
        wait_time = timeout or self.timeout
        try:
            return WebDriverWait(self.driver, wait_time).until(
                EC.url_contains(partial_url)
            )
        except TimeoutException:
            logger.error(f"La URL '{self.driver.current_url}' no contuvo '{partial_url}' tras {wait_time}s")
            return False
