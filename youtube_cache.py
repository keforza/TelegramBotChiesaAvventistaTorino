"""
Gestione della cache YouTube del bot Telegram.
"""

import logging

from commands.ricercaculto import (
    load_culti_from_youtube,
    set_culti_cache,
)

from commands.ricercadiretta import (
    load_dirette_from_youtube,
    set_dirette_cache,
)


# ==================================================
# LOG
# ==================================================

logger = logging.getLogger(
    "TelegramBot.YouTubeCache"
)


# ==================================================
# AGGIORNAMENTO CACHE YOUTUBE
# ==================================================

async def youtube_cache_update(context):
    """
    Aggiorna la cache di YouTube.

    I comandi Telegram non interrogano direttamente
    YouTube: utilizzano esclusivamente i dati presenti
    nelle rispettive cache.
    """

    try:

        logger.info(
            "🔄 Aggiornamento cache YouTube..."
        )

        # ------------------------------------------
        # CARICAMENTO CULTI
        # ------------------------------------------

        culti = await load_culti_from_youtube()

        # ------------------------------------------
        # CARICAMENTO DIRETTE
        # ------------------------------------------

        dirette = await load_dirette_from_youtube()

        # ------------------------------------------
        # AGGIORNAMENTO CACHE
        # ------------------------------------------

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