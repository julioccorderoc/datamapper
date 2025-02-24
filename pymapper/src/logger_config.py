import logging
import inspect

class ContextualFormatter(logging.Formatter):
    def format(self, record):
        # Go up the call stack to find the actual calling function
        frame = inspect.currentframe()
        depth = 0
        while frame and depth < 6:
            code = frame.f_code
            if code.co_name not in ('emit', 'format', 'handle', 'callHandlers', 'makeRecord'):
                record.funcName = code.co_name
                break
            frame = frame.f_back
            depth += 1

        return super().format(record)

def setup_logger(logger_name: str, log_level_name: str = "ERROR") -> logging.Logger:
    logger = logging.getLogger(logger_name)
    formatter = ContextualFormatter('%(asctime)s | %(levelname)s | %(name)s | %(funcName)s >>> %(message)s',
                                    datefmt='%Y-%m-%d %H:%M:%S')

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        log_level = getattr(logging, log_level_name.upper(), logging.INFO)
        logger.setLevel(log_level)

    return logger
