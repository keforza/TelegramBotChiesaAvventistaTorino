"""
Configurazione del logging del Bot Telegram.
"""

import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# ==================================================
# RIDUZIONE LOG LIBRERIE ESTERNE
# ==================================================

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)


# ==================================================
# LOGGER PRINCIPALE
# ==================================================

logger = logging.getLogger("TelegramBot")