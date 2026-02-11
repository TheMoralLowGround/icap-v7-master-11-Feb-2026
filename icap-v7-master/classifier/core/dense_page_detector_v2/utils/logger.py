import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(processName)s] [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Suppress noisy debug logs from PIL
logging.getLogger("PIL").setLevel(logging.INFO)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.INFO)

logger = logging.getLogger(__name__)