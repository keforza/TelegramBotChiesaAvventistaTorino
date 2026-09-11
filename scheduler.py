"""
Gestione della schedulazione automatica del bot.
"""

import datetime

from config import (
    ROME_TIMEZONE,
    YOUTUBE_CACHE_DURATION,
)

from logger import logger

from notifications import (
    send_latest_diretta,
)

from youtube_cache import (
    youtube_cache_update,
)


# ==================================================
# CONFIGURAZIONE SCHEDULER
# ==================================================

def configure_scheduler(application):
    """
    Configura tutti i job automatici del bot.
    """

    # ----------------------------------------------
    # CACHE YOUTUBE
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