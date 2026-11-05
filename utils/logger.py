import logging
from logging.handlers import RotatingFileHandler
from utils.config import LOG_FILE, LOGS_DIR

# Asegurar existencia de la carpeta de logs
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FORMAT = "%(asctime)s [%(levelname)8s] %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_file_logging() -> logging.Logger:
    """Configura el sistema de logging centralizado con rotación de archivos en UTF-8."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Evitar duplicar el FileHandler si ya fue registrado en la sesión
    log_path_str = str(LOG_FILE.resolve())
    has_file_handler = any(
        isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", "") == log_path_str
        for h in root_logger.handlers
    )

    if not has_file_handler:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=1024 * 1024,  # 1 MB por archivo
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        root_logger.addHandler(file_handler)

    return logging.getLogger("qa_framework")


# Instancia global lista para importar en cualquier módulo
logger = configure_file_logging()
