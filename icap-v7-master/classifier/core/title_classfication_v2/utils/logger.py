"""
Centralized logging configuration for title classification module.
"""
import logging
import sys

# Module-level logger name
LOGGER_NAME = "auto_classificaton"

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance for the title classification module.

    Args:
        name: Optional sub-logger name. If provided, creates a child logger.
              e.g., get_logger("classifier") -> "auto_classificaton.classifier"

    Returns:
        logging.Logger: Configured logger instance
    """
    if name:
        return logging.getLogger(f"{LOGGER_NAME}.{name}")
    return logging.getLogger(LOGGER_NAME)


def setup_logger(
    level: int = logging.INFO,
    format_string: str = None,
    stream_handler: bool = True
) -> logging.Logger:
    """
    Configure the root logger for the title classification module.

    Args:
        level: Logging level (default: INFO)
        format_string: Custom format string (optional)
        stream_handler: Whether to add a stream handler to stdout (default: True)

    Returns:
        logging.Logger: Configured root logger
    """
    logger = logging.getLogger(LOGGER_NAME)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(level)

    if format_string is None:
        format_string = "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s"

    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    if stream_handler:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# Initialize logger with default configuration on module import
_logger = setup_logger()
