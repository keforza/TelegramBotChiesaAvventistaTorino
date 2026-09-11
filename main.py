"""
Modulo principale del Bot Telegram.
"""

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
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

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)

from logger import logger

from scheduler import (
    post_init,
    start_heartbeat,
)

from utils import (
    format_search_terms,
    format_user,
)


# ==================================================
# WRAPPER /START
# ==================================================

async def logged_start(update, context):
    user = update.effective_user

    logger.info(
        "📥 /start richiesto da %s",
        format_user(user),
    )

    await start(update, context)


# ==================================================
# WRAPPER /CULTO
# ==================================================

async def logged_ricercaculto(update, context):
    user = update.effective_user

    logger.info(
        "📥 /culto richiesto da %s | ricerca: %s",
        format_user(user),
        format_search_terms(context),
    )

    await ricercaculto(update, context)


# ==================================================
# WRAPPER /DIRETTA
# ==================================================

async def logged_ricercadiretta(update, context):
    user = update.effective_user

    logger.info(
        "📥 /diretta richiesto da %s | ricerca: %s",
        format_user(user),
        format_search_terms(context),
    )

    await ricercadiretta(update, context)


# ==================================================
# NAVIGAZIONE CULTI
# ==================================================

async def logged_culto_navigation(update, context):
    user = update.effective_user
    query = update.callback_query

    logger.info(
        "🔘 Pulsante culto premuto da %s: %s",
        format_user(user),
        query.data if query else "sconosciuto",
    )

    await culto_navigation(
        update,
        context,
    )


# ==================================================
# NAVIGAZIONE DIRETTE
# ==================================================

async def logged_diretta_navigation(update, context):
    user = update.effective_user
    query = update.callback_query

    logger.info(
        "🔘 Pulsante diretta premuto da %s: %s",
        format_user(user),
        query.data if query else "sconosciuto",
    )

    await diretta_navigation(
        update,
        context,
    )


# ==================================================
# MAIN
# ==================================================

def main():

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN non trovato nel file .env"
        )

    if not TELEGRAM_CHAT_ID:
        raise RuntimeError(
            "TELEGRAM_CHAT_ID non trovato nel file .env"
        )

    logger.info(
        "🚀 Avvio del bot Telegram..."
    )

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

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
    # CALLBACK CULTI
    # ----------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            logged_culto_navigation,
            pattern=r"^culto_(prev|next|position)$",
        )
    )

    # ----------------------------------------------
    # CALLBACK DIRETTE
    # ----------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            logged_diretta_navigation,
            pattern=r"^diretta_(prev|next|position)$",
        )
    )

    # ----------------------------------------------
    # HEARTBEAT
    # ----------------------------------------------

    start_heartbeat()

    logger.info(
        "🤖 Bot pronto. In ascolto dei comandi..."
    )

    application.run_polling(
        drop_pending_updates=True
    )


# ==================================================
# AVVIO
# ==================================================

if __name__ == "__main__":
    main()