"""
Gestione della programmazione dei job automatici.
"""

import datetime
import threading
import time

from config import (
    ROME_TIMEZONE,
    YOUTUBE_CACHE_DURATION,
)

from logger import logger

from notifications import (
    send_latest_diretta,
)

from telegram_commands import (
    configure_bot_commands,
)

from youtube_cache import (
    youtube_cache_update,
)


# ==================================================
# POST INIT
# ==================================================

async def post_init(application):
    """
    Configura comandi e avvia gli scheduler.
    """

    # ----------------------------------------------
    # COMANDI TELEGRAM
    # ----------------------------------------------

    await configure_bot_commands(
        application
    )

    # ----------------------------------------------
    # PRIMO AGGIORNAMENTO CACHE
    # ----------------------------------------------

    await youtube_cache_update()

    # ----------------------------------------------
    # CACHE YOUTUBE OGNI ORA
    # ----------------------------------------------

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

    # ----------------------------------------------
    # ULTIMA DIRETTA
    # ----------------------------------------------

    application.job_queue.run_daily(
        send_latest_diretta,
        time=datetime.time(
            hour=18,
            minute=1,
            tzinfo=ROME_TIMEZONE,
        ),
        days=(4,),
        name="latest_diretta_thursday",
    )

    logger.info(
        "📅 Invio ultima diretta programmato: "
        "ogni giovedì alle 18:01."
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
            "🟢 BOT ATTIVO E FUNZIONANTE"
        )


# ==================================================
# AVVIO HEARTBEAT
# ==================================================

def start_heartbeat():
    """
    Avvia il thread heartbeat.
    """

    threading.Thread(
        target=heartbeat,
        daemon=True,
    ).start()