"""
Configurazione dei comandi Telegram.
"""

from telegram import BotCommand
from telegram import BotCommandScopeAllPrivateChats
from telegram import BotCommandScopeChat

from config import TELEGRAM_CHAT_ID
from logger import logger


# ==================================================
# COMANDI CHAT PRIVATA
# ==================================================

PRIVATE_COMMANDS = [
    BotCommand(
        "start",
        "Avvia il bot",
    ),
    BotCommand(
        "culto",
        "Cerca un culto",
    ),
    BotCommand(
        "diretta",
        "Cerca una diretta",
    ),
]


# ==================================================
# CONFIGURAZIONE COMANDI
# ==================================================

async def configure_bot_commands(application):
    """
    Configura i comandi visibili nelle chat private
    e nel gruppo configurato.
    """

    # ----------------------------------------------
    # CHAT PRIVATE
    # ----------------------------------------------

    try:
        await application.bot.set_my_commands(
            commands=PRIVATE_COMMANDS,
            scope=BotCommandScopeAllPrivateChats(),
        )

        logger.info(
            "🟢 Comandi configurati per le chat private."
        )

    except Exception:
        logger.exception(
            "❌ Errore configurazione comandi chat private."
        )

    # ----------------------------------------------
    # GRUPPO
    # ----------------------------------------------

    if not TELEGRAM_CHAT_ID:
        logger.warning(
            "⚠️ TELEGRAM_CHAT_ID non configurato: "
            "comandi del gruppo non configurati."
        )
        return

    try:
        try:
            chat_id = int(TELEGRAM_CHAT_ID)
        except ValueError:
            chat_id = TELEGRAM_CHAT_ID

        await application.bot.set_my_commands(
            commands=[
                BotCommand(
                    "culto",
                    "Cerca un culto",
                ),
                BotCommand(
                    "diretta",
                    "Cerca una diretta",
                ),
            ],
            scope=BotCommandScopeChat(
                chat_id=chat_id,
            ),
        )

        logger.info(
            "🟢 Comandi configurati per il gruppo."
        )

    except Exception:
        logger.exception(
            "❌ Errore configurazione comandi gruppo."
        )