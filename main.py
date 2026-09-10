"""
Modulo principale per l'esecuzione del Bot Telegram.
Gestione comandi, caching YouTube, schedulazione e comandi effimeri.
"""

import datetime
import logging
import os
import threading
import time
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# ==================================================
# CARICAMENTO VARIABILI .ENV
# ==================================================
load_dotenv(".env")

# ==================================================
# IMPORT TELEGRAM
# ==================================================
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
)

# ==================================================
# IMPORT COMANDI
# ==================================================
from commands.start import start
from commands.ricercaculto import (
    ricercaculto,
    culto_navigation,
    load_culti_from_youtube,
    set_culti_cache,
)
from commands.ricercadiretta import (
    ricercadiretta,
    diretta_navigation,
    load_dirette_from_youtube,
    set_dirette_cache,
    get_all_dirette,
)

# ==================================================
# CONFIGURAZIONE
# ==================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ROME_TIMEZONE = ZoneInfo("Europe/Rome")

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
logger = logging.getLogger("TelegramBot")

# ==================================================
# RIDUZIONE LOG ESTERNI
# ==================================================
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)


# ==================================================
# CONFIGURAZIONE COMANDI EPHEMERAL
# ==================================================
async def configure_ephemeral_commands(application):
    """
    Configura /culto e /diretta come comandi
    effimeri esclusivamente nel gruppo configurato
    in TELEGRAM_CHAT_ID.
    """
    if not TELEGRAM_CHAT_ID:
        logger.warning(
            "⚠️ TELEGRAM_CHAT_ID non configurato: "
            "comandi ephemeral non configurati."
        )
        return

    try:
        try:
            chat_id = int(TELEGRAM_CHAT_ID)
        except ValueError:
            chat_id = TELEGRAM_CHAT_ID

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
            },
        )

        logger.info(
            "🔒 Comandi ephemeral configurati per il gruppo %s.",
            TELEGRAM_CHAT_ID,
        )

    except Exception:
        logger.exception("❌ Impossibile configurare i comandi ephemeral.")


# ==================================================
# AGGIORNAMENTO CACHE YOUTUBE
# ==================================================
async def youtube_cache_update(context):
    """
    Aggiorna la cache di YouTube.
    I comandi Telegram NON interrogano YouTube.
    """
    try:
        logger.info("🔄 Aggiornamento cache YouTube...")

        culti = await load_culti_from_youtube()
        dirette = await load_dirette_from_youtube()

        set_culti_cache(culti)
        set_dirette_cache(dirette)

        logger.info(
            "🟢 Cache YouTube aggiornata: %d culti, %d dirette.",
            len(culti),
            len(dirette),
        )

    except Exception:
        logger.exception("❌ Errore aggiornamento cache YouTube.")


# ==================================================
# INVIO AUTOMATICO ULTIMA DIRETTA
# ==================================================
async def send_latest_diretta(context):
    """
    Invia automaticamente l'ultima diretta
    TERMINATA presente nella cache.
    Questo messaggio rimane PUBBLICO.
    """
    if not TELEGRAM_CHAT_ID:
        logger.error("❌ TELEGRAM_CHAT_ID non configurato.")
        return

    try:
        logger.info("📤 Scheduler: preparazione invio ultima diretta...")

        dirette = get_all_dirette()
        dirette_terminate = [
            diretta for diretta in dirette if diretta.get("actual_end_time")
        ]

        if not dirette_terminate:
            logger.warning(
                "⚠️ Scheduler: nessuna diretta terminata disponibile nella cache."
            )
            return

        latest = max(
            dirette_terminate,
            key=lambda diretta: diretta.get("actual_end_time", ""),
        )

        title = latest.get("title", "Diretta senza titolo")
        video_url = latest.get("url", "")
        thumbnail = latest.get("thumbnail", "")
        actual_end_time = latest.get("actual_end_time", "")

        formatted_date = actual_end_time
        try:
            date = datetime.datetime.fromisoformat(
                actual_end_time.replace("Z", "+00:00")
            )
            date = date.astimezone(ROME_TIMEZONE)
            formatted_date = date.strftime("%d/%m/%Y alle %H:%M")
        except Exception:
            pass

        caption = (
            "🔴 <b>Ultima diretta</b>\n\n"
            f"⛪ <b>{title}</b>\n\n"
            f"📅 Terminata: {formatted_date}"
        )

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

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

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
            "❌ Errore durante l'invio automatico dell'ultima diretta."
        )


# ==================================================
# AVVIO CACHE E SCHEDULER
# ==================================================
async def post_init(application):
    """
    Esegue il primo aggiornamento della cache
    e programma gli aggiornamenti automatici.
    """
    await configure_ephemeral_commands(application)
    await youtube_cache_update(None)

    application.job_queue.run_repeating(
        youtube_cache_update,
        interval=YOUTUBE_CACHE_DURATION,
        first=YOUTUBE_CACHE_DURATION,
        name="youtube_cache",
    )

    logger.info("🕐 Scheduler cache YouTube attivo.")
    logger.info("⏳ Prossimo aggiornamento YouTube tra 1 ora.")

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

    logger.info("📅 Invio ultima diretta programmato: ogni giovedì alle 18:01.")


# ==================================================
# HEARTBEAT
# ==================================================
def heartbeat():
    """
    Mostra periodicamente che il bot è attivo.
    """
    while True:
        time.sleep(600)
        logger.info("🟢 BOT ATTIVO E FUNZIONANTE")


# ==================================================
# FORMATTA TERMINE DI RICERCA
# ==================================================
def format_search_terms(context):
    """
    Restituisce gli argomenti utilizzati dopo il comando.
    """
    args = getattr(context, "args", None)
    if not args:
        return "nessun termine"
    return " ".join(args)


# ==================================================
# FORMATTA UTENTE
# ==================================================
def format_user(user):
    """
    Restituisce un identificativo leggibile dell'utente per i log.
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
async def logged_start(update, context):
    """
    Wrapper per registrare l'utilizzo di /start.
    """
    user = update.effective_user
    logger.info("📥 /start richiesto da %s", format_user(user))
    await start(update, context)


async def logged_ricercaculto(update, context):
    """
    Wrapper per registrare l'utilizzo di /culto e il termine cercato.
    """
    user = update.effective_user
    search_terms = format_search_terms(context)
    logger.info(
        "📥 /culto richiesto da %s | ricerca: %s",
        format_user(user),
        search_terms,
    )
    await ricercaculto(update, context)


async def logged_ricercadiretta(update, context):
    """
    Wrapper per registrare l'utilizzo di /diretta e il termine cercato.
    """
    user = update.effective_user
    search_terms = format_search_terms(context)
    logger.info(
        "📥 /diretta richiesto da %s | ricerca: %s",
        format_user(user),
        search_terms,
    )
    await ricercadiretta(update, context)


async def logged_culto_navigation(update, context):
    """
    Wrapper per registrare la navigazione dei culti.
    """
    user = update.effective_user
    query = update.callback_query
    logger.info(
        "🔘 Pulsante culto premuto da %s: %s",
        format_user(user),
        query.data if query else "sconosciuto",
    )
    await culto_navigation(update, context)


async def logged_diretta_navigation(update, context):
    """
    Wrapper per registrare la navigazione delle dirette.
    """
    user = update.effective_user
    query = update.callback_query
    logger.info(
        "🔘 Pulsante diretta premuto da %s: %s",
        format_user(user),
        query.data if query else "sconosciuto",
    )
    await diretta_navigation(update, context)


# ==================================================
# MAIN
# ==================================================
def main():
    """
    Avvia il bot Telegram.
    """
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN non trovato nel file .env")

    if not TELEGRAM_CHAT_ID:
        raise RuntimeError("TELEGRAM_CHAT_ID non trovato nel file .env")

    logger.info("🚀 Avvio del bot Telegram...")

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Handlers Comandi
    application.add_handler(CommandHandler("start", logged_start))
    application.add_handler(CommandHandler("culto", logged_ricercaculto))
    application.add_handler(CommandHandler("diretta", logged_ricercadiretta))

    # Handlers Paginazione Callback
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

    # Thread heartbeat
    threading.Thread(target=heartbeat, daemon=True).start()

    logger.info("🟢 Bot pronto. In ascolto dei comandi...")
    application.run_polling(drop_pending_updates=True)


# ==================================================
# AVVIO PROGRAMMA
# ==================================================
if __name__ == "__main__":
    main()