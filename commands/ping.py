"""
Comando /ping riservato all'amministratore.

Il comando è effimero.
La risposta è effimera.
"""

import os
import time

from telegram import Update
from telegram.ext import ContextTypes


async def ping(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    # ==================================================
    # CONTROLLO AMMINISTRATORE
    # ==================================================

    admin_id = os.getenv("ADMIN_TELEGRAM_ID")

    if not admin_id:
        return

    user = update.effective_user

    if user is None:
        return

    if str(user.id) != str(admin_id):
        return

    # ==================================================
    # CONTROLLO CHAT
    # ==================================================

    chat = update.effective_chat

    if chat is None:
        return

    # ==================================================
    # MISURA LATENZA TELEGRAM
    # ==================================================

    start_time = time.perf_counter()

    await context.bot.get_me()

    latency = (
        time.perf_counter() - start_time
    ) * 1000

    # ==================================================
    # RISPOSTA EFFIMERA
    # ==================================================

    await context.bot.do_api_request(
        "sendMessage",
        {
            "chat_id": chat.id,
            "text": (
                "🏓 Pong!\n"
                f"⚡ Latenza: {latency:.0f} ms"
            ),
            "ephemeral_message_parameters": {
                "receiver_user_id": user.id,
            },
        },
    )