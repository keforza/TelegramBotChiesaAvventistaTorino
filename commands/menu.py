"""
Comando di test per il menu Telegram.
"""

from telegram import Update
from telegram.ext import ContextTypes


async def menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Comando di test /menu.
    """

    await update.effective_message.reply_text(
        "🧪 Menu di test"
    )