"""
Comando /ping riservato all'amministratore.

Il comando /ping è effimero.
La risposta è effimera.
Entrambi sono visibili solamente all'amministratore.
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
    Risponde al comando /ping con:

    🏓 Pong!
    ⚡ Latenza: XX ms

    Il comando e la risposta sono entrambi ephemeral.
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

    # ==================================================
    # RECUPERA L'ID DEL COMANDO EPHEMERAL
    # ==================================================

    message = update.effective_message

    if message is None:
        return

    # PTB potrebbe non esporre il campo direttamente.
    ephemeral_message_id = getattr(
        message,
        "ephemeral_message_id",
        None,
    )

    # Fallback: controlliamo il dizionario dell'Update.
    if ephemeral_message_id is None:
        update_data = update.to_dict()

        message_data = update_data.get(
            "message",
            {},
        )

        ephemeral_message_id = message_data.get(
            "ephemeral_message_id"
        )

    # Se Telegram non ci ha fornito l'ID,
    # NON inviamo una risposta normale.
    if ephemeral_message_id is None:
        return

    # ==================================================
    # MISURA DELLA LATENZA
    # ==================================================
    #
    # Usiamo una chiamata reale al Bot API.
    #
    # getMe() non modifica nulla e ci permette di
    # misurare il tempo di andata/ritorno Telegram.
    # ==================================================

    start_time = time.perf_counter()

    await context.bot.get_me()

    latency = (
        time.perf_counter() - start_time
    ) * 1000

    # ==================================================
    # RISPOSTA EPHEMERAL
    # ==================================================
    #
    # Rispondendo all'ephemeral_message_id,
    # Telegram rende automaticamente ephemeral
    # anche questa risposta.
    #
    # Questa è L'UNICA risposta inviata dal bot.
    # ==================================================

    await context.bot.do_api_request(
        "sendMessage",
        {
            "chat_id": chat.id,
            "text": (
                "🏓 Pong!\n"
                f"⚡ Latenza: {latency:.0f} ms"
            ),
            "reply_parameters": {
                "ephemeral_message_id": ephemeral_message_id,
            },
        },
    )