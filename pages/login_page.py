from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from utils.config import BASE_URL
import logging

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """Page Object para la página de autenticación de SauceDemo."""

    # Localizadores de la página de Login
    USERNAME_INPUT = (By.ID, "user-name")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.ID, "login-button")
    ERROR_MESSAGE = (By.CSS_SELECTOR, "[data-test='error']")
    LOGIN_LOGO = (By.CLASS_NAME, "login_logo")

    def __init__(self, driver):
        super().__init__(driver)
        self.url = BASE_URL

    def load(self) -> "LoginPage":
        """Navega a la página de inicio de sesión de SauceDemo."""
        self.open_url(self.url)
        # Esperar a que el botón de login esté visible para confirmar carga completa
        self.find_element(self.LOGIN_BUTTON)
        return self

    def enter_username(self, username: str) -> "LoginPage":
        """Escribe el nombre de usuario en el campo correspondiente."""
        self.type_text(self.USERNAME_INPUT, username)
        return self

    def enter_password(self, password: str) -> "LoginPage":
        """Escribe la contraseña en el campo correspondiente."""
        self.type_text(self.PASSWORD_INPUT, password)
        return self

    def click_login(self) -> None:
        """Hace clic en el botón de login."""
        self.click(self.LOGIN_BUTTON)

    def login(self, username: str, password: str) -> None:
        """Flujo completo de inicio de sesión: usuario, contraseña y clic."""
        logger.info(f"Iniciando sesión con usuario: {username}")
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()

    def get_error_message(self) -> str:
        """Obtiene el texto del mensaje de error si las credenciales fallan."""
        return self.get_text(self.ERROR_MESSAGE)

    def is_login_page_loaded(self) -> bool:
        """Verifica si la página de login está completamente cargada."""
        return self.is_visible(self.LOGIN_BUTTON) and self.is_visible(self.LOGIN_LOGO)
