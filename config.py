"""
Configurazione principale del Bot Telegram.
"""

import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


load_dotenv(".env")


# ==================================================
# TELEGRAM
# ==================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ==================================================
# TIMEZONE
# ==================================================

ROME_TIMEZONE = ZoneInfo("Europe/Rome")


# ==================================================
# CACHE YOUTUBE
# ==================================================

YOUTUBE_CACHE_DURATION = 3600