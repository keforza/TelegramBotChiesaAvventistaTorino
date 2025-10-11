from flask import Flask
from dotenv import load_dotenv
import os
import aiohttp
import datetime
import logging
import pytz
import threading

# Importa da telegram.ext
from telegram.ext import ApplicationBuilder, CommandHandler
# Assicurati che "commands.ultimovideo" esista e contenga handle_ultimovideo
from commands.ultimovideo import handle_ultimovideo 

# 🔧 Flask setup
app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, World!"

def run_flask():
    # La porta 5000 è comune, usa la variabile d'ambiente PORT per la compatibilità con hosting
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# 🔐 Carica variabili d'ambiente - 📢 CORREZIONE QUI
# Assicurati che 'script_dati.env' sia nella stessa cartella
load_dotenv("script_dati.env")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 🕒 Fuso orario e orario di pubblicazione
ITALY_TZ = pytz.timezone("Europe/Rome")
POST_HOUR = 10
POST_MINUTE = 45

# 📝 Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 📺 Funzione per ottenere l'ultimo video (resta invariata)
async def get_latest_video():
    # ... (il codice per get_latest_video è corretto)
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={CHANNEL_ID}&type=video&order=date&key={YOUTUBE_API_KEY}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

        logger.info(f"API Response: {data}")

        if "items" in data and data["items"]:
            video_id = data["items"][0]["id"]["videoId"]
            video_title = data["items"][0]["snippet"]["title"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            logger.info(f"Found latest video: {video_title} ({video_url})")
            return video_title, video_url
        else:
            logger.info("No videos found.")
            return None, None
    except aiohttp.ClientError as e:
        logger.error(f"Error fetching video: {e}")
        return None, None

# 📤 Funzione JobQueue - sostituisce il loop manuale
async def post_to_telegram_job(context):
    """Chiama get_latest_video e invia il messaggio usando l'istanza Bot fornita dal JobQueue."""
    logger.info("Tentativo di invio automatico del video.")
    
    title, url = await get_latest_video()
    
    if title and url:
        message = f"🎥 Ultimo video: {title}\n🔴 Guarda qui: {url}"
    else:
        message = "Nessun video recente trovato."

    try:
        # 📢 CORREZIONE QUI: Usa context.bot e la variabile globale CHAT_ID
        await context.bot.send_message(chat_id=CHAT_ID, text=message)
        logger.info("Messaggio Telegram inviato con JobQueue.")
    except Exception as e:
        logger.error(f"Errore nell'invio del messaggio su Telegram (JobQueue): {e}")

# 🚀 Avvio bot Telegram con JobQueue - 📢 CORREZIONE QUI
def run_telegram():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # 1. Aggiungi il gestore di comando
    application.add_handler(CommandHandler("ultimovideo", handle_ultimovideo))

    # 2. Configura il JobQueue per lo scheduling
    job_queue = application.job_queue
    
    # Crea un oggetto time per l'orario di pubblicazione in fuso orario ITALY_TZ
    post_time = datetime.time(hour=POST_HOUR, minute=POST_MINUTE, tzinfo=ITALY_TZ)
    
    # Pianifica l'esecuzione per ogni Sabato (5) all'orario specificato
    job_queue.run_daily(
        post_to_telegram_job,
        time=post_time,
        days=(5,), # 5 = Sabato (Lunedì è 0)
        name="daily_video_post"
    )

    # 3. Avvia il polling (che gestisce anche il JobQueue)
    application.run_polling()

# 🧵 Avvio dei thread
if __name__ == "__main__":
    logger.info("Avvio del server Flask e del bot Telegram in thread separati.")
    
    flask_thread = threading.Thread(target=run_flask)
    telegram_thread = threading.Thread(target=run_telegram)

    flask_thread.start()
    telegram_thread.start()

    flask_thread.join()
    telegram_thread.join()