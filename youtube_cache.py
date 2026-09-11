"""
Gestione della cache YouTube del bot.
"""

from commands.ricercaculto import (
    load_culti_from_youtube,
    set_culti_cache,
)

from commands.ricercadiretta import (
    load_dirette_from_youtube,
    set_dirette_cache,
)

from logger import logger


# ==================================================
# AGGIORNAMENTO CACHE
# ==================================================

async def update_youtube_cache():
    """
    Scarica i dati da YouTube e aggiorna
    le cache utilizzate dai comandi Telegram.

    I comandi Telegram non interrogano direttamente
    YouTube: utilizzano sempre la cache.
    """

    try:

        logger.info(
            "🔄 Aggiornamento cache YouTube..."
        )

        culti = await load_culti_from_youtube()

        dirette = await load_dirette_from_youtube()

        set_culti_cache(culti)

        set_dirette_cache(dirette)

        logger.info(
            "🟢 Cache YouTube aggiornata: "
            "%d culti, %d dirette.",
            len(culti),
            len(dirette),
        )

    except Exception:

        logger.exception(
            "❌ Errore aggiornamento cache YouTube."
        )


# ==================================================
# JOB TELEGRAM
# ==================================================

async def youtube_cache_update(context):
    """
    Wrapper compatibile con JobQueue di python-telegram-bot.
    """

    await update_youtube_cache()