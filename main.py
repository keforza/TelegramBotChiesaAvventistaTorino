import datetime
import logging
import os
import threading

import aiohttp
import pytz
from dotenv import load_dotenv
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler

from commands.ricercaculto import handle_ricercaculto


load_dotenv(".env")


YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


required_variables = {
    "YOUTUBE_API_KEY": YOUTUBE_API_KEY,
    "CHANNEL_ID": CHANNEL_ID,
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "CHAT_ID": CHAT_ID,
}

missing_variables = [
    name for name, value in required_variables.items() if not value
]


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


app = Flask(__name__)


@app.route("/")
def home():
    return "Hello, World!"


def run_flask():
    """Avvia il server Flask."""

    port = int(os.environ.get("PORT", 5000))

    logger.info(
        "Avvio server Flask sulla porta %s.",
        port
    )

    app.run(
        host="0.0.0.0",
        port=port
    )


async def get_latest_video():
    """Recupera l'ultimo video pubblicato sul canale YouTube."""

    url = (
        "https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet"
        f"&channelId={CHANNEL_ID}"
        f"&type=video"
        f"&order=date"
        f"&key={YOUTUBE_API_KEY}"
    )

    try:

        async with aiohttp.ClientSession() as session:

            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

        if not data.get("items"):
            logger.info("Nessun video trovato.")
            return None, None

        video = data["items"][0]

        video_id = video["id"]["videoId"]
        video_title = video["snippet"]["title"]

        video_url = (
            f"https://www.youtube.com/watch?v={video_id}"
        )

        logger.info(
            "Ultimo video trovato: %s",
            video_title
        )

        return video_title, video_url

    except aiohttp.ClientError as error:

        logger.error(
            "Errore durante la richiesta alle YouTube API: %s",
            error
        )

    except (KeyError, TypeError) as error:

        logger.error(
            "Risposta YouTube non valida: %s",
            error
        )

    return None, None


async def post_to_telegram_job(context):
    """Recupera l'ultimo video YouTube e lo pubblica nella chat Telegram."""

    logger.info(
        "Tentativo di invio automatico del video."
    )

    title, url = await get_latest_video()

    message = (
        f"🎥 Ultimo video: {title}\n"
        f"🔴 Guarda qui: {url}"
        if title and url
        else "Nessun video recente trovato."
    )

    try:

        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=message
        )

        logger.info(
            "Messaggio Telegram inviato correttamente."
        )

    except Exception as error:

        logger.error(
            "Errore nell'invio del messaggio Telegram: %s",
            error
        )


def run_telegram():
    """Avvia il bot Telegram."""

    logger.info(
        "Avvio del bot Telegram."
    )

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Comando /culto
    application.add_handler(
        CommandHandler(
            "culto",
            handle_ricercaculto
        )
    )

    italy_tz = pytz.timezone(
        "Europe/Rome"
    )

    post_time = datetime.time(
        hour=10,
        minute=45,
        tzinfo=italy_tz
    )

    application.job_queue.run_daily(
        post_to_telegram_job,
        time=post_time,
        days=(5,),
        name="weekly_video_post",
    )

    logger.info(
        "Job automatico configurato: sabato alle 10:45."
    )

    application.run_polling()


if __name__ == "__main__":

    logger.info(
        "Avvio del sistema..."
    )

    if missing_variables:

        logger.error(
            "Mancano alcune variabili nel file .env: %s",
            ", ".join(missing_variables)
        )

        raise RuntimeError(
            "Configurazione .env incompleta."
        )

    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    telegram_thread = threading.Thread(
        target=run_telegram,
        daemon=True
    )

    flask_thread.start()
    telegram_thread.start()

    logger.info(
        "Flask e Telegram sono stati avviati."
    )

    flask_thread.join()
    telegram_thread.join()