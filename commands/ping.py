"""
Comando /ping riservato all'amministratore.

Il comando e la risposta sono completamente effimeri.
"""

import os
import time

from telegram import Update
from telegram.ext import ContextTypes


async def ping(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Misura la latenza tra il bot e Telegram.

    Il comando è utilizzabile solamente dall'amministratore.
    La risposta è effimera.
    """

    # ==================================================
    # CONTROLLO AMMINISTRATORE
    # ==================================================

    admin_id = os.getenv(
        "ADMIN_TELEGRAM_ID"
    )

    if not admin_id:
        return

    user = update.effective_user

    if not user:
        return

    if str(user.id) != str(admin_id):
        return

    chat = update.effective_chat

    if not chat:
        return

    # ==================================================
    # INVIO MESSAGGIO EPHEMERAL
    # ==================================================

    start_time = time.perf_counter()

    message = await context.bot.send_message(
        chat_id=chat.id,
        text="🏓 Pong...",
        api_kwargs={
            "ephemeral_message_parameters": {
                "receiver_user_id": user.id,
            }
        },
    )

    # ==================================================
    # CALCOLO LATENZA
    # ==================================================

    latency = (
        time.perf_counter() - start_time
    ) * 1000

    # ==================================================
    # CONTROLLO ID MESSAGGIO EPHEMERAL
    # ==================================================

    ephemeral_message_id = getattr(
        message,
        "ephemeral_message_id",
        None,
    )

    if not ephemeral_message_id:
        return

    # ==================================================
    # AGGIORNA MESSAGGIO EPHEMERAL
    # ==================================================

    await context.bot.do_api_request(
        "editEphemeralMessageText",
        {
            "chat_id": chat.id,
            "receiver_user_id": user.id,
            "ephemeral_message_id": ephemeral_message_id,
            "text": (
                f"🏓 Pong!\n"
                f"⚡ Latenza: {latency:.0f} ms"
            ),
        },
    )