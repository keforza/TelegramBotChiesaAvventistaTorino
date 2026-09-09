import logging
import os
import threading
import time

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler

from commands.start import start


load_dotenv(".env")


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Evita di mostrare nei log le richieste HTTP
# che possono contenere il token del bot nell'URL.
logging.getLogger("httpx").setLevel(logging.WARNING)


def heartbeat():
    """Mostra periodicamente che il bot è ancora attivo."""

    while True:
        time.sleep(30)
        logger.info("🟢 Bot attivo e in ascolto")


def main():
    """Avvia il bot Telegram."""

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN non trovato nel file .env"
        )

    logger.info("Avvio del bot Telegram...")

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Comando /start
    application.add_handler(
        CommandHandler("start", start)
    )

    logger.info("Bot avviato correttamente.")

    # Avvia il controllo di attività in background.
    threading.Thread(
        target=heartbeat,
        daemon=True,
    ).start()

    application.run_polling()


if __name__ == "__main__":
    main()