"""
Configurazione del sistema di logging del bot.
"""

import logging


# ==================================================
# CONFIGURAZIONE LOGGING
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# ==================================================
# LOGGER PRINCIPALE
# ==================================================

logger = logging.getLogger(
    "TelegramBot"
)


# ==================================================
# RIDUZIONE LOG ESTERNI
# ==================================================

logging.getLogger(
    "httpx"
).setLevel(logging.WARNING)

logging.getLogger(
    "httpcore"
).setLevel(logging.WARNING)

logging.getLogger(
    "telegram"
).setLevel(logging.WARNING)

logging.getLogger(
    "telegram.ext"
).setLevel(logging.WARNING)

logging.getLogger(
    "apscheduler"
).setLevel(logging.WARNING)