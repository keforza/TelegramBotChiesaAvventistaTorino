"""
Gestione delle notifiche automatiche del bot.
"""

import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from config import (
    TELEGRAM_CHAT_ID,
    ROME_TIMEZONE,
)

from commands.ricercadiretta import (
    get_all_dirette,
)

from logger import logger


# ==================================================
# ULTIMA DIRETTA
# ==================================================

async def send_latest_diretta(context):
    """
    Invia automaticamente l'ultima diretta terminata
    presente nella cache.

    Questo messaggio è PUBBLICO.
    Non viene utilizzato il sistema ephemeral.
    """

    if not TELEGRAM_CHAT_ID:

        logger.error(
            "❌ TELEGRAM_CHAT_ID non configurato."
        )

        return

    try:

        logger.info(
            "📤 Scheduler: preparazione invio "
            "ultima diretta..."
        )

        dirette = get_all_dirette()

        dirette_terminate = [
            diretta
            for diretta in dirette
            if diretta.get("actual_end_time")
        ]

        if not dirette_terminate:

            logger.warning(
                "⚠️ Scheduler: nessuna diretta "
                "terminata disponibile nella cache."
            )

            return

        latest = max(
            dirette_terminate,
            key=lambda diretta: diretta.get(
                "actual_end_time",
                "",
            ),
        )

        title = latest.get(
            "title",
            "Diretta senza titolo",
        )

        video_url = latest.get(
            "url",
            "",
        )

        thumbnail = latest.get(
            "thumbnail",
            "",
        )

        actual_end_time = latest.get(
            "actual_end_time",
            "",
        )

        # ------------------------------------------
        # FORMATTAZIONE DATA
        # ------------------------------------------

        formatted_date = actual_end_time

        try:

            date = datetime.datetime.fromisoformat(
                actual_end_time.replace(
                    "Z",
                    "+00:00",
                )
            )

            date = date.astimezone(
                ROME_TIMEZONE
            )

            formatted_date = date.strftime(
                "%d/%m/%Y alle %H:%M"
            )

        except Exception:

            pass

        # ------------------------------------------
        # CAPTION
        # ------------------------------------------

        caption = (
            "🔴 <b>Ultima diretta</b>\n\n"
            f"⛪ <b>{title}</b>\n\n"
            f"📅 Terminata: {formatted_date}"
        )

        # ------------------------------------------
        # PULSANTE YOUTUBE
        # ------------------------------------------

        keyboard = []

        if video_url:

            keyboard.append(
                [
                    InlineKeyboardButton(
                        "▶️ Guarda la diretta",
                        url=video_url,
                    )
                ]
            )

        reply_markup = (
            InlineKeyboardMarkup(keyboard)
            if keyboard
            else None
        )

        # ------------------------------------------
        # INVIO
        # ------------------------------------------

        if thumbnail:

            await context.bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=thumbnail,
                caption=caption,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )

        else:

            await context.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=caption,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )

        logger.info(
            '📨 Ultima diretta inviata: "%s" | '
            "terminata: %s",
            title,
            formatted_date,
        )

    except Exception:

        logger.exception(
            "❌ Errore durante l'invio automatico "
            "dell'ultima diretta."
        )