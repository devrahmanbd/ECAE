import logging
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler(console=__import__('rich.console').console.Console(stderr=True))]
)

logger = logging.getLogger("ecae_lite")
