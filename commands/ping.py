"""
Comando /ping riservato all'amministratore.
"""

import os
import time

from telegram import Update
from telegram.ext import ContextTypes


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Misura la latenza tra il bot e le API di Telegram.
    Il comando è utilizzabile solamente dall'amministratore.
    """

    admin_id = os.getenv("ADMIN_TELEGRAM_ID")

    if not admin_id:
        await update.message.reply_text(
            "❌ ADMIN_TELEGRAM_ID non configurato."
        )
        return

    if str(update.effective_user.id) != str(admin_id):
        await update.message.reply_text(
            "⛔ Non hai i permessi per utilizzare questo comando."
        )
        return

    start_time = time.perf_counter()

    message = await update.message.reply_text(
        "🏓 Pong..."
    )

    latency = (
        time.perf_counter() - start_time
    ) * 1000

    await message.edit_text(
        f"🏓 Pong!\n"
        f"⚡ Latenza: {latency:.0f} ms"
    )