"""
Notifiche automatiche del Bot Telegram.
"""

import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from commands.ricercadiretta import get_all_dirette

from config import (
    TELEGRAM_CHAT_ID,
    ROME_TIMEZONE,
)

from logger import logger


# ==================================================
# FORMATTA DURATA
# ==================================================

def format_duration(start_time, end_time):
    """
    Calcola la durata della diretta.
    """

    if not start_time or not end_time:
        return "sconosciuta"

    try:
        start_date = datetime.datetime.fromisoformat(
            start_time.replace("Z", "+00:00")
        )

        end_date = datetime.datetime.fromisoformat(
            end_time.replace("Z", "+00:00")
        )

        seconds = max(
            0,
            int(
                (end_date - start_date).total_seconds()
            ),
        )

        hours, remainder = divmod(
            seconds,
            3600,
        )

        minutes, seconds = divmod(
            remainder,
            60,
        )

        if hours > 0:
            return f"{hours}h {minutes:02d}min"

        return f"{minutes}min {seconds:02d}s"

    except Exception:
        return "sconosciuta"


# ==================================================
# FORMATTA DATA
# ==================================================

def format_end_date(end_time):
    """
    Converte la data di fine diretta nel formato italiano.
    """

    if not end_time:
        return "sconosciuta"

    try:
        date = datetime.datetime.fromisoformat(
            end_time.replace("Z", "+00:00")
        )

        date = date.astimezone(
            ROME_TIMEZONE
        )

        return date.strftime(
            "%d/%m/%Y alle %H:%M"
        )

    except Exception:
        return end_time


# ==================================================
# INVIO ULTIMA DIRETTA
# ==================================================

async def send_latest_diretta(context):
    """
    Invia automaticamente l'ultima diretta terminata
    presente nella cache.
    """

    if not TELEGRAM_CHAT_ID:
        logger.error(
            "❌ TELEGRAM_CHAT_ID non configurato."
        )
        return

    try:
        logger.info(
            "📤 Preparazione invio ultima diretta..."
        )

        dirette = get_all_dirette()

        # ------------------------------------------
        # SOLO DIRETTE TERMINATE
        # ------------------------------------------

        dirette_terminate = [
            diretta
            for diretta in dirette
            if diretta.get("actual_end_time")
        ]

        if not dirette_terminate:
            logger.warning(
                "⚠️ Nessuna diretta terminata "
                "disponibile nella cache."
            )
            return

        # ------------------------------------------
        # ULTIMA DIRETTA
        # ------------------------------------------

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

        actual_start_time = latest.get(
            "actual_start_time",
            "",
        )

        actual_end_time = latest.get(
            "actual_end_time",
            "",
        )

        # ------------------------------------------
        # DURATA
        # ------------------------------------------

        duration = format_duration(
            actual_start_time,
            actual_end_time,
        )

        # ------------------------------------------
        # DATA
        # ------------------------------------------

        formatted_date = format_end_date(
            actual_end_time
        )

        # ------------------------------------------
        # DIDASCALIA
        # ------------------------------------------

        caption = (
            "🔴 <b>Ultima diretta</b>\n\n"
            f"⛪ <b>{title}</b>\n\n"
            f"⏱️ Durata: {duration}\n\n"
            f"📅 Terminata: {formatted_date}"
        )

        # ------------------------------------------
        # PULSANTE
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
            '📨 Ultima diretta inviata: "%s" | terminata: %s',
            title,
            formatted_date,
        )

    except Exception:
        logger.exception(
            "❌ Errore durante l'invio automatico "
            "dell'ultima diretta."
        )