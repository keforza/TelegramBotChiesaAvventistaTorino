"""
Comando /ping riservato all'amministratore.

Il comando e la risposta sono completamente effimeri.
Gli altri utenti del gruppo non possono vedere la risposta.
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
    La risposta è effimera e visibile esclusivamente
    all'utente che ha eseguito il comando.
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

    message = update.effective_message

    if not message:
        return

    # ==================================================
    # RECUPERA ID DEL MESSAGGIO EPHEMERAL
    # ==================================================

    ephemeral_message_id = getattr(
        message,
        "ephemeral_message_id",
        None,
    )

    if not ephemeral_message_id:
        return

    # ==================================================
    # MISURA LATENZA
    # ==================================================

    start_time = time.perf_counter()

    # ==================================================
    # INVIA UN'UNICA RISPOSTA EPHEMERAL
    # ==================================================

    latency = (
        time.perf_counter() - start_time
    ) * 1000

    await context.bot.send_message(
        chat_id=chat.id,
        text=(
            f"🏓 Pong!\n"
            f"⚡ Latenza: {latency:.0f} ms"
        ),
        reply_parameters={
            "ephemeral_message_id": ephemeral_message_id,
        },
    )