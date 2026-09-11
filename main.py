"""
Modulo principale per l'esecuzione del Bot Telegram.
"""

import threading
import time


from telegram.ext import (
    ApplicationBuilder,
)


from config import (
    TELEGRAM_BOT_TOKEN,
)

from logger import logger

from youtube_cache import (
    update_youtube_cache,
)

from scheduler import (
    configure_scheduler,
)

from telegram_commands import (
    configure_ephemeral_commands,
    register_handlers,
)


# ==================================================
# POST INIT
# ==================================================

async def post_init(application):
    """
    Inizializzazione eseguita dopo la creazione
    dell'applicazione Telegram.
    """

    # ----------------------------------------------
    # COMANDI EPHEMERAL
    # ----------------------------------------------

    await configure_ephemeral_commands(
        application
    )

    # ----------------------------------------------
    # PRIMO AGGIORNAMENTO CACHE
    # ----------------------------------------------

    await update_youtube_cache()

    # ----------------------------------------------
    # SCHEDULER
    # ----------------------------------------------

    configure_scheduler(
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

    logger.info(
        "🚀 Avvio del bot Telegram..."
    )

    # ----------------------------------------------
    # APPLICATION
    # ----------------------------------------------

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ----------------------------------------------
    # HANDLERS
    # ----------------------------------------------

    register_handlers(
        application
    )

    # ----------------------------------------------
    # HEARTBEAT
    # ----------------------------------------------

    threading.Thread(
        target=heartbeat,
        daemon=True,
    ).start()

    logger.info(
        "🟢 Bot pronto. "
        "In ascolto dei comandi..."
    )

    # ----------------------------------------------
    # POLLING
    # ----------------------------------------------

    application.run_polling(
        drop_pending_updates=True
    )


# ==================================================
# AVVIO PROGRAMMA
# ==================================================

if __name__ == "__main__":
    main()