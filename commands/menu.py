"""
Comando di test per la tastiera rapida.
"""

from telegram import (
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes


async def menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Mostra la tastiera rapida di test.
    """

    keyboard = [
        ["📖 Test Culto", "📺 Test Diretta"],
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )

    await update.effective_message.reply_text(
        "🧪 Tastiera di test:",
        reply_markup=reply_markup,
    )