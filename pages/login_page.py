from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from utils.config import BASE_URL
import logging

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """Page Object para la página de autenticación de SauceDemo."""

    # =========================================================================
    # Localizadores de la página de Login (Estrategia priorizada: ID > data-test > CLASS_NAME)
    # =========================================================================
    # Campo de texto para el nombre de usuario (atributo id='user-name' único en el DOM)
    USERNAME_INPUT = (By.ID, "user-name")
    # Campo de texto enmascarado para la contraseña (atributo id='password' único en el DOM)
    PASSWORD_INPUT = (By.ID, "password")
    # Botón principal de envío del formulario de autenticación (atributo id='login-button')
    LOGIN_BUTTON = (By.ID, "login-button")
    # Contenedor dinámico de alertas de error de autenticación (selector CSS por atributo data-test='error')
    ERROR_MESSAGE = (By.CSS_SELECTOR, "[data-test='error']")
    # Logotipo superior 'Swag Labs' en la pantalla de inicio de sesión (clase CSS 'login_logo')
    LOGIN_LOGO = (By.CLASS_NAME, "login_logo")

    def __init__(self, driver):
        super().__init__(driver)
        self.url = BASE_URL

    def load(self) -> "LoginPage":
        """Navega a la página de inicio de sesión de SauceDemo."""
        self.open_url(self.url)
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
        logger.info(f"Iniciando sesión con usuario: '{username}'")
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()

    def is_error_displayed(self) -> bool:
        """Verifica si el contenedor de mensaje de error está visible en pantalla."""
        return self.is_visible(self.ERROR_MESSAGE)

    def get_error_message(self) -> str:
        """Obtiene el texto del mensaje de error cuando las credenciales son inválidas."""
        return self.get_text(self.ERROR_MESSAGE)

    def is_login_page_loaded(self) -> bool:
        """Verifica si la página de login está completamente cargada."""
        return self.is_visible(self.LOGIN_BUTTON) and self.is_visible(self.LOGIN_LOGO)
