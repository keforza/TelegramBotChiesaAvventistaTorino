"""
Gestione dei comandi e degli handler Telegram.
"""

from telegram import (
    BotCommand,
    BotCommandScopeChat,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
)

from config import TELEGRAM_CHAT_ID

from logger import logger

from utils import (
    format_search_terms,
    format_user,
)

from commands.start import start

from commands.ricercaculto import (
    ricercaculto,
    culto_navigation,
)

from commands.ricercadiretta import (
    ricercadiretta,
    diretta_navigation,
)


# ==================================================
# CONFIGURAZIONE COMANDI EPHEMERAL
# ==================================================

async def configure_ephemeral_commands(application):
    """
    Configura /culto e /diretta come comandi
    effimeri esclusivamente nel gruppo configurato.

    Utilizza direttamente Bot.set_my_commands()
    invece di do_api_request().
    """

    if not TELEGRAM_CHAT_ID:

        logger.warning(
            "⚠️ TELEGRAM_CHAT_ID non configurato: "
            "comandi ephemeral non configurati."
        )

        return

    try:

        try:
            chat_id = int(
                TELEGRAM_CHAT_ID
            )

        except ValueError:

            chat_id = TELEGRAM_CHAT_ID

        commands = [
            BotCommand(
                command="culto",
                description="Cerca un culto",
                api_kwargs={
                    "is_ephemeral": True,
                },
            ),
            BotCommand(
                command="diretta",
                description="Cerca una diretta",
                api_kwargs={
                    "is_ephemeral": True,
                },
            ),
        ]

        scope = BotCommandScopeChat(
            chat_id=chat_id
        )

        await application.bot.set_my_commands(
            commands=commands,
            scope=scope,
        )

        logger.info(
            "🔒 Comandi ephemeral configurati "
            "per il gruppo %s.",
            TELEGRAM_CHAT_ID,
        )

    except Exception:

        logger.exception(
            "❌ Impossibile configurare "
            "i comandi ephemeral."
        )


# ==================================================
# LOG /START
# ==================================================

async def logged_start(
    update,
    context,
):
    """
    Wrapper per registrare l'utilizzo di /start.
    """

    user = update.effective_user

    logger.info(
        "📥 /start richiesto da %s",
        format_user(user),
    )

    await start(
        update,
        context,
    )


# ==================================================
# LOG /CULTO
# ==================================================

async def logged_ricercaculto(
    update,
    context,
):
    """
    Wrapper per registrare l'utilizzo di /culto.
    """

    user = update.effective_user

    search_terms = format_search_terms(
        context
    )

    logger.info(
        "📥 /culto richiesto da %s | "
        "ricerca: %s",
        format_user(user),
        search_terms,
    )

    await ricercaculto(
        update,
        context,
    )


# ==================================================
# LOG /DIRETTA
# ==================================================

async def logged_ricercadiretta(
    update,
    context,
):
    """
    Wrapper per registrare l'utilizzo di /diretta.
    """

    user = update.effective_user

    search_terms = format_search_terms(
        context
    )

    logger.info(
        "📥 /diretta richiesto da %s | "
        "ricerca: %s",
        format_user(user),
        search_terms,
    )

    await ricercadiretta(
        update,
        context,
    )


# ==================================================
# LOG NAVIGAZIONE CULTO
# ==================================================

async def logged_culto_navigation(
    update,
    context,
):
    """
    Wrapper per registrare la navigazione
    dei risultati dei culti.
    """

    user = update.effective_user

    query = update.callback_query

    logger.info(
        "🔘 Pulsante culto premuto da %s: %s",
        format_user(user),
        query.data
        if query
        else "sconosciuto",
    )

    await culto_navigation(
        update,
        context,
    )


# ==================================================
# LOG NAVIGAZIONE DIRETTA
# ==================================================

async def logged_diretta_navigation(
    update,
    context,
):
    """
    Wrapper per registrare la navigazione
    delle dirette.
    """

    user = update.effective_user

    query = update.callback_query

    logger.info(
        "🔘 Pulsante diretta premuto da %s: %s",
        format_user(user),
        query.data
        if query
        else "sconosciuto",
    )

    await diretta_navigation(
        update,
        context,
    )


# ==================================================
# REGISTRAZIONE HANDLER
# ==================================================

def register_handlers(application):
    """
    Registra tutti gli handler Telegram.
    """

    # ----------------------------------------------
    # COMANDI
    # ----------------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            logged_start,
        )
    )

    application.add_handler(
        CommandHandler(
            "culto",
            logged_ricercaculto,
        )
    )

    application.add_handler(
        CommandHandler(
            "diretta",
            logged_ricercadiretta,
        )
    )

    # ----------------------------------------------
    # PAGINAZIONE CULTO
    # ----------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            logged_culto_navigation,
            pattern=r"^culto_(prev|next|position)$",
        )
    )

    # ----------------------------------------------
    # PAGINAZIONE DIRETTA
    # ----------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            logged_diretta_navigation,
            pattern=r"^diretta_(prev|next|position)$",
        )
    )

    logger.info(
        "🧩 Handler Telegram registrati."
    )