"""
logger_config.py
==============


"""

import os
import logging
import inspect

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class ContextualFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Traverse call stack to find the actual calling function
        frame = inspect.currentframe()
        depth = 0
        while frame and depth < 6:
            code = frame.f_code
            if code.co_name not in (
                "emit",
                "format",
                "handle",
                "callHandlers",
                "makeRecord",
            ):
                record.funcName = code.co_name
                break
            frame = frame.f_back
            depth += 1
        return super().format(record)


def configure_logger() -> logging.Logger:
    """Configure datamapper logger with environment-aware settings"""
    logger = logging.getLogger("datamapper")
    logger.setLevel(logging.DEBUG)  # Base level for all handlers
    logger.propagate = False  # Prevent root logger interference

    formatter = ContextualFormatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(funcName)s >>> %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler setup
    console_level_name = os.getenv("LOG_LEVEL_datamapper", "ERROR").upper()
    # console_level = os.getenv("LOG_LEVEL_datamapper", "ERROR").upper()
    console_level = getattr(logging, console_level_name, logging.ERROR)

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler setup
    log_file_path = os.getenv("LOG_FILE_datamapper")
    if log_file_path:
        file_level_name = os.getenv("LOG_FILE_LEVEL_datamapper", "INFO").upper()
        # file_level = os.getenv("LOG_FILE_LEVEL_datamapper", "INFO").upper()
        file_level = getattr(logging, file_level_name, logging.INFO)

        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        # Prevent duplicate file handlers
        if not any(
            h.baseFilename == os.path.abspath(log_file_path)
            for h in logger.handlers
            if isinstance(h, logging.FileHandler)
        ):
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(file_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


logger = configure_logger()
