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

    message = update.effective_message

    if message is None:
        return

    # ==================================================
    # RECUPERA ID DEL MESSAGGIO EPHEMERAL
    # ==================================================

    ephemeral_message_id = getattr(
        message,
        "ephemeral_message_id",
        None,
    )

    # Fallback nel caso PTB non esponga direttamente
    # il campo sulla classe Message.
    if ephemeral_message_id is None:
        update_data = update.to_dict()

        message_data = update_data.get(
            "message",
            {},
        )

        ephemeral_message_id = message_data.get(
            "ephemeral_message_id"
        )

    # Se il comando non è effettivamente ephemeral,
    # non inviamo nessuna risposta normale.
    if ephemeral_message_id is None:
        return

    # ==================================================
    # MISURA LATENZA
    # ==================================================

    start_time = time.perf_counter()

    # ==================================================
    # RISPOSTA EPHEMERAL
    # ==================================================

    await context.bot.send_message(
        chat_id=chat.id,
        text="🏓 Pong!",
        reply_parameters={
            "ephemeral_message_id": ephemeral_message_id,
        },
    )

    # ==================================================
    # CALCOLO LATENZA
    # ==================================================

    latency = (
        time.perf_counter() - start_time
    ) * 1000

    # ==================================================
    # AGGIORNAMENTO DELLA RISPOSTA
    # ==================================================

    await context.bot.do_api_request(
        "editEphemeralMessageText",
        {
            "chat_id": chat.id,
            "message_id": ephemeral_message_id,
            "text": (
                "🏓 Pong!\n"
                f"⚡ Latenza: {latency:.0f} ms"
            ),
        },
    )