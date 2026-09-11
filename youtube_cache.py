"""
Gestione della cache YouTube.
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

async def youtube_cache_update(context=None):
    """
    Aggiorna la cache di YouTube.

    I comandi Telegram non interrogano direttamente
    YouTube: utilizzano i dati presenti nella cache.
    """

    logger.info(
        "🔄 Aggiornamento cache YouTube..."
    )

    # ----------------------------------------------
    # CULTI
    # ----------------------------------------------

    try:
        culti = await load_culti_from_youtube()

    except Exception:
        logger.exception(
            "❌ Errore aggiornamento cache culti YouTube."
        )

        culti = []

    # ----------------------------------------------
    # DIRETTE
    # ----------------------------------------------

    try:
        dirette = await load_dirette_from_youtube()

    except Exception:
        logger.exception(
            "❌ Errore aggiornamento cache dirette YouTube."
        )

        dirette = []

    # ----------------------------------------------
    # SALVATAGGIO CULTI
    # ----------------------------------------------

    try:
        set_culti_cache(culti)

        logger.info(
            "🟢 Cache culti aggiornata: %d culti.",
            len(culti),
        )

    except Exception:
        logger.exception(
            "❌ Errore salvataggio cache culti."
        )

    # ----------------------------------------------
    # SALVATAGGIO DIRETTE
    # ----------------------------------------------

    try:
        set_dirette_cache(dirette)

        logger.info(
            "🟢 Cache dirette aggiornata: %d dirette.",
            len(dirette),
        )

    except Exception:
        logger.exception(
            "❌ Errore salvataggio cache dirette."
        )

    logger.info(
        "🟢 Cache YouTube aggiornata: %d culti, %d dirette.",
        len(culti),
        len(dirette),
    )