"""
Modulo principale per l'esecuzione del Bot Telegram.

Gestione avvio bot, comandi, callback,
comandi ephemeral, heartbeat e server HTTP Render.
"""

import logging
import os
import threading
import time

from dotenv import load_dotenv
from flask import Flask


# ==================================================
# CARICAMENTO VARIABILI .ENV
# ==================================================

load_dotenv(".env")


# ==================================================
# IMPORT TELEGRAM
# ==================================================

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
)


# ==================================================
# IMPORT COMANDI
# ==================================================

from commands.start import start

from commands.ping import ping

from commands.ricercaculto import (
    ricercaculto,
    culto_navigation,
)

from commands.ricercadiretta import (
    ricercadiretta,
    diretta_navigation,
)


# ==================================================
# IMPORT CACHE YOUTUBE
# ==================================================

from youtube_cache import (
    youtube_cache_update,
)


# ==================================================
# IMPORT SCHEDULER
# ==================================================

from scheduler import (
    setup_scheduler,
)


# ==================================================
# CONFIGURAZIONE
# ==================================================

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID"
)

ADMIN_TELEGRAM_ID = os.getenv(
    "ADMIN_TELEGRAM_ID"
)


# ==================================================
# CACHE YOUTUBE
# ==================================================

YOUTUBE_CACHE_DURATION = 3600


# ==================================================
# LOG
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

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


# ==================================================
# SERVER HTTP PER RENDER
# ==================================================

flask_app = Flask(__name__)


@flask_app.route("/")
def health_check():
    """
    Endpoint utilizzato da Render per verificare
    che il servizio HTTP sia attivo.
    """

    return "Telegram Bot is running", 200


def start_http_server():
    """
    Avvia il piccolo server HTTP richiesto da Render.
    """

    port = int(
        os.getenv(
            "PORT",
            10000,
        )
    )

    logger.info(
        "🌐 Server HTTP avviato sulla porta %d.",
        port,
    )

    flask_app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )


# ==================================================
# CONFIGURAZIONE COMANDI EPHEMERAL
# ==================================================

async def configure_ephemeral_commands(
    application,
):
    """
    Configura i comandi ephemeral.

    Utenti normali:
        /culto
        /diretta

    Amministratore:
        /culto
        /diretta
        /ping
    """

    if not TELEGRAM_CHAT_ID:

        logger.warning(
            "⚠️ TELEGRAM_CHAT_ID non configurato: "
            "comandi ephemeral non configurati."
        )

        return

    if not ADMIN_TELEGRAM_ID:

        logger.warning(
            "⚠️ ADMIN_TELEGRAM_ID non configurato: "
            "comandi admin non configurati."
        )

        return

    try:

        try:

            chat_id = int(
                TELEGRAM_CHAT_ID
            )

        except ValueError:

            chat_id = TELEGRAM_CHAT_ID

        try:

            admin_id = int(
                ADMIN_TELEGRAM_ID
            )

        except ValueError:

            logger.error(
                "❌ ADMIN_TELEGRAM_ID non è un numero valido."
            )

            return

        # ==================================================
        # COMANDI VISIBILI A TUTTI
        # ==================================================

        user_commands = [
            {
                "command": "culto",
                "description": "Cerca un culto",
                "is_ephemeral": True,
            },
            {
                "command": "diretta",
                "description": "Cerca una diretta",
                "is_ephemeral": True,
            },
        ]

        await application.bot.do_api_request(
            "setMyCommands",
            {
                "commands": user_commands,
                "scope": {
                    "type": "chat",
                    "chat_id": chat_id,
                },
                "language_code": "",
            },
        )

        # ==================================================
        # COMANDI VISIBILI SOLO ALL'ADMIN
        # ==================================================

        admin_commands = [
            {
                "command": "culto",
                "description": "Cerca un culto",
                "is_ephemeral": True,
            },
            {
                "command": "diretta",
                "description": "Cerca una diretta",
                "is_ephemeral": True,
            },
            {
                "command": "ping",
                "description": "Controlla la latenza del bot",
                "is_ephemeral": True,
            },
        ]

        await application.bot.do_api_request(
            "setMyCommands",
            {
                "commands": admin_commands,
                "scope": {
                    "type": "chat_member",
                    "chat_id": chat_id,
                    "user_id": admin_id,
                },
                "language_code": "",
            },
        )

        logger.info(
            "🔒 Comandi ephemeral configurati: "
            "/culto e /diretta per tutti, "
            "/ping solo per l'amministratore."
        )

        # ==================================================
        # VERIFICA LISTA GENERALE
        # ==================================================

        user_result = await application.bot.do_api_request(
            "getMyCommands",
            {
                "scope": {
                    "type": "chat",
                    "chat_id": chat_id,
                },
                "language_code": "",
            },
        )

        logger.info(
            "🔎 Comandi utenti: %s",
            user_result,
        )

        # ==================================================
        # VERIFICA LISTA ADMIN
        # ==================================================

        admin_result = await application.bot.do_api_request(
            "getMyCommands",
            {
                "scope": {
                    "type": "chat_member",
                    "chat_id": chat_id,
                    "user_id": admin_id,
                },
                "language_code": "",
            },
        )

        logger.info(
            "🔎 Comandi admin: %s",
            admin_result,
        )

    except Exception:

        logger.exception(
            "❌ Impossibile configurare "
            "i comandi ephemeral."
        )


# ==================================================
# POST INIT
# ==================================================

async def post_init(
    application,
):
    """
    Esegue la configurazione iniziale del bot,
    aggiorna la cache YouTube e registra
    gli scheduler.
    """

    await configure_ephemeral_commands(
        application
    )

    await youtube_cache_update(
        None
    )

    application.job_queue.run_repeating(
        youtube_cache_update,
        interval=YOUTUBE_CACHE_DURATION,
        first=YOUTUBE_CACHE_DURATION,
        name="youtube_cache",
    )

    logger.info(
        "🕐 Scheduler cache YouTube attivo."
    )

    logger.info(
        "⏳ Prossimo aggiornamento YouTube "
        "tra 1 ora."
    )

    setup_scheduler(
        application
    )


# ==================================================
# HEARTBEAT
# ==================================================

def heartbeat():
    """
    Mostra periodicamente che il bot è attivo.
    """

    while True:

        time.sleep(600)

        logger.info(
            "🟢 Bot attivo e funzionante"
        )


# ==================================================
# FORMATTA TERMINE DI RICERCA
# ==================================================

def format_search_terms(
    context,
):
    """
    Restituisce gli argomenti utilizzati
    dopo il comando.
    """

    args = getattr(
        context,
        "args",
        None,
    )

    if not args:

        return "nessun termine"

    return " ".join(
        args
    )


# ==================================================
# FORMATTA UTENTE
# ==================================================

def format_user(
    user,
):
    """
    Restituisce un identificativo leggibile
    dell'utente per i log.
    """

    if not user:

        return "utente sconosciuto"

    if user.username:

        return f"@{user.username}"

    if user.full_name:

        return user.full_name

    return f"id={user.id}"


# ==================================================
# LOG COMANDI E INTERAZIONI UTENTE
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


async def logged_ping(
    update,
    context,
):
    """
    Wrapper per registrare l'utilizzo di /ping.
    """

    user = update.effective_user

    logger.info(
        "📥 /ping richiesto da %s",
        format_user(user),
    )

    await ping(
        update,
        context,
    )


async def logged_ricercaculto(
    update,
    context,
):
    """
    Wrapper per registrare l'utilizzo di /culto
    e il termine cercato.
    """

    user = update.effective_user

    search_terms = format_search_terms(
        context
    )

    logger.info(
        "📥 /culto richiesto da %s | ricerca: %s",
        format_user(user),
        search_terms,
    )

    await ricercaculto(
        update,
        context,
    )


async def logged_ricercadiretta(
    update,
    context,
):
    """
    Wrapper per registrare l'utilizzo di /diretta
    e il termine cercato.
    """

    user = update.effective_user

    search_terms = format_search_terms(
        context
    )

    logger.info(
        "📥 /diretta richiesto da %s | ricerca: %s",
        format_user(user),
        search_terms,
    )

    await ricercadiretta(
        update,
        context,
    )


async def logged_culto_navigation(
    update,
    context,
):
    """
    Wrapper per registrare la navigazione dei culti.
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
# MAIN
# ==================================================

def main():
    """
    Avvia il bot Telegram.
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

    logger.info(
        "🚀 Avvio del bot Telegram..."
    )

    # ==================================================
    # SERVER HTTP RENDER
    # ==================================================

    threading.Thread(
        target=start_http_server,
        daemon=True,
    ).start()

    application = (
        ApplicationBuilder()
        .token(
            TELEGRAM_BOT_TOKEN
        )
        .post_init(
            post_init
        )
        .build()
    )

    # ==================================================
    # HANDLERS COMANDI
    # ==================================================

    application.add_handler(
        CommandHandler(
            "start",
            logged_start,
        )
    )

    application.add_handler(
        CommandHandler(
            "ping",
            logged_ping,
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

    # ==================================================
    # HANDLERS PAGINAZIONE CALLBACK
    # ==================================================

    application.add_handler(
        CallbackQueryHandler(
            logged_culto_navigation,
            pattern=r"^culto_(prev|next|position)$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            logged_diretta_navigation,
            pattern=r"^diretta_(prev|next|position)$",
        )
    )

    # ==================================================
    # THREAD HEARTBEAT
    # ==================================================

    threading.Thread(
        target=heartbeat,
        daemon=True,
    ).start()

    # ==================================================
    # AVVIO
    # ==================================================

    logger.info(
        "🟢 Bot pronto. In ascolto dei comandi..."
    )

    application.run_polling(
        drop_pending_updates=True
    )


# ==================================================
# AVVIO PROGRAMMA
# ==================================================

if __name__ == "__main__":

    main()