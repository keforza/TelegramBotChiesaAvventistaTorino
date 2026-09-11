"""
Configurazione centrale del Telegram Bot.
"""

import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


# ==================================================
# CARICAMENTO .ENV
# ==================================================

load_dotenv(".env")


# ==================================================
# TELEGRAM
# ==================================================

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID"
)


# ==================================================
# TIMEZONE
# ==================================================

ROME_TIMEZONE = ZoneInfo(
    "Europe/Rome"
)


# ==================================================
# YOUTUBE CACHE
# ==================================================

YOUTUBE_CACHE_DURATION = 3600


# ==================================================
# VALIDAZIONE CONFIGURAZIONE
# ==================================================

def validate_config():
    """
    Verifica che le variabili obbligatorie
    siano presenti.
    """

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN non trovato "
            "nel file .env"
        )

    if not TELEGRAM_CHAT_ID:
        raise RuntimeError(
            "TELEGRAM_CHAT_ID non trovato "
            "nel file .env"
        )