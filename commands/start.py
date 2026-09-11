from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /start."""

    await update.message.reply_text(
        "👋 Ciao! Benvenuto nel bot!"
    )