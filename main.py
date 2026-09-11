"""
Modulo principale per l'esecuzione del Bot Telegram.
"""

import contextlib
import io
import logging
import os
import threading
import time
import warnings

from dotenv import load_dotenv
from flask import Flask

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
)

from commands.start import start
from commands.ricercaculto import ricercaculto, culto_navigation
from commands.ricercadiretta import ricercadiretta, diretta_navigation
from youtube_cache import youtube_cache_update
from scheduler import setup_scheduler


# ==================================================
# CONFIGURAZIONE
# ==================================================

load_dotenv(".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")

YOUTUBE_CACHE_DURATION = 3600


# ==================================================
# LOGGING
# ==================================================

warnings.filterwarnings(
    "ignore",
    message=r".*Please use .* instead of .*",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("TelegramBot")

for name in (
    "httpx",
    "httpcore",
    "telegram",
    "telegram.ext",
    "apscheduler",
):
    logging.getLogger(name).setLevel(logging.WARNING)

logging.getLogger("werkzeug").disabled = True


# ==================================================
# SERVER HTTP
# ==================================================

flask_app = Flask(__name__)
flask_app.logger.disabled = True


@flask_app.route("/")
def health_check():
    return "Il Bot di Telegram è in esecuzione", 200


def start_http_server():
    port = int(os.getenv("PORT", 10000))

    logger.info("🌐 Server HTTP attivo sulla porta %s.", port)

    with contextlib.redirect_stdout(io.StringIO()):
        flask_app.run(
            host="0.0.0.0",
            port=port,
            debug=False,
            use_reloader=False,
        )


# ==================================================
# COMANDI EPHEMERAL
# ==================================================

async def configure_ephemeral_commands(application):

    if not TELEGRAM_CHAT_ID:
        logger.warning("⚠️ TELEGRAM_CHAT_ID non configurato.")
        return

    try:
        try:
            chat_id = int(TELEGRAM_CHAT_ID)
        except ValueError:
            chat_id = TELEGRAM_CHAT_ID

        if ADMIN_TELEGRAM_ID:
            try:
                try:
                    admin_id = int(ADMIN_TELEGRAM_ID)
                except ValueError:
                    admin_id = ADMIN_TELEGRAM_ID

                await application.bot.do_api_request(
                    "deleteMyCommands",
                    {
                        "scope": {
                            "type": "chat_member",
                            "chat_id": chat_id,
                            "user_id": admin_id,
                        },
                        "language_code": "",
                    },
                )
            except Exception:
                pass

        commands = [
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

        scope = {
            "type": "chat",
            "chat_id": chat_id,
        }

        await application.bot.do_api_request(
            "setMyCommands",
            {
                "commands": commands,
                "scope": scope,
                "language_code": "",
            },
        )

        logger.info(
            "🔒 Comandi ephemeral configurati per il gruppo %s.",
            TELEGRAM_CHAT_ID,
        )

        await application.bot.do_api_request(
            "getMyCommands",
            {
                "scope": scope,
                "language_code": "",
            },
        )

    except Exception:
        logger.exception(
            "❌ Errore configurazione comandi ephemeral."
        )


# ==================================================
# AVVIO APPLICATION
# ==================================================

async def post_init(application):

    await configure_ephemeral_commands(application)

    await youtube_cache_update(None)

    application.job_queue.run_repeating(
        youtube_cache_update,
        interval=YOUTUBE_CACHE_DURATION,
        first=YOUTUBE_CACHE_DURATION,
        name="youtube_cache",
    )

    logger.info("🕐 Scheduler cache YouTube attivo.")

    setup_scheduler(application)


# ==================================================
# HEARTBEAT
# ==================================================

def heartbeat():
    while True:
        time.sleep(600)


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

    logger.info("🚀 Avvio del bot Telegram...")

    threading.Thread(
        target=start_http_server,
        daemon=True,
    ).start()

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("culto", ricercaculto)
    )

    application.add_handler(
        CommandHandler("diretta", ricercadiretta)
    )

    application.add_handler(
        CallbackQueryHandler(
            culto_navigation,
            pattern=r"^culto_(prev|next|position)$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            diretta_navigation,
            pattern=r"^diretta_(prev|next|position)$",
        )
    )

    threading.Thread(
        target=heartbeat,
        daemon=True,
    ).start()

    logger.info("🟢 Bot pronto. In ascolto dei comandi...")

    application.run_polling(
        drop_pending_updates=True
    )


# ==================================================
# AVVIO
# ==================================================

if __name__ == "__main__":
    main()