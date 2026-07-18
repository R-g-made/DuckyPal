import logging
import sys
from app.core.config import settings

def setup_logger():
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )
    return logging.getLogger("UtyaPal")

logger = setup_logger()
