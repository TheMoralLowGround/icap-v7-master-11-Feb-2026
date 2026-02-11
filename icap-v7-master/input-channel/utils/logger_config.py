import logging
from datetime import datetime, timezone

LEVEL_COLORS = {
    'error': '\033[91m',
    'info': '\033[92m',
    'warning': '\033[93m',
    'debug': '\033[94m',
    'critical': '\033[95m'
}
RESET = '\033[0m'

LOG_LEVEL = logging.DEBUG

class LogFormatter(logging.Formatter):
    """Custom formatter with microseconds and timezone offset"""

    def formatTime(self, record, datefmt=None):
        """Get UTC timestamp with timezone info"""
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return dt.isoformat(sep=' ', timespec='microseconds')

    def format(self, record):
        record.asctime = self.formatTime(record)
        level = record.levelname.lower()
        color = LEVEL_COLORS.get(level, '')
        message = f"{record.asctime} [{level}] {record.getMessage()}"
        return f"{color}{message}{RESET}"

def get_logger(name):
    """Return a logger that output to console with formatted timestamp"""

    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(LOG_LEVEL)
        console_handler.setFormatter(LogFormatter())
        logger.addHandler(console_handler)

    return logger