import logging
import os
from logging.handlers import RotatingFileHandler
from utils.config import LOG_FILE, LOGS_DIR

# Asegurar existencia de la carpeta de logs
LOGS_DIR.mkdir(parents=True, exist_ok=True)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_file_logging() -> logging.Logger:
    """Configura el sistema de logging centralizado con rotación de archivos en UTF-8.

    Soporta ejecución paralela con pytest-xdist identificando el worker activo (ej. gw0, gw1)
    y evitando colisiones de bloqueo de archivos entre procesos concurrentes en Windows/Linux.
    """
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "main")
    log_format = f"%(asctime)s [%(levelname)8s] [{worker_id}] %(name)s - %(message)s"

    target_log_file = (
        LOG_FILE if worker_id == "main" else LOGS_DIR / f"suite_{worker_id}.log"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    log_path_str = str(target_log_file.resolve())
    has_file_handler = any(
        isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", "") == log_path_str
        for h in root_logger.handlers
    )

    if not has_file_handler:
        file_handler = RotatingFileHandler(
            target_log_file,
            maxBytes=1024 * 1024,  # 1 MB por archivo
            backupCount=5,
            encoding="utf-8",
            delay=True,
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(log_format, datefmt=DATE_FORMAT))
        root_logger.addHandler(file_handler)

    return logging.getLogger("qa_framework")


# Instancia global lista para importar en cualquier módulo
logger = configure_file_logging()
