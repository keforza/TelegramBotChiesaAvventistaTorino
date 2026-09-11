from telegram import Update
from telegram.ext import ContextTypes

from ephemeral import is_group_update, send_text as send_ephemeral_text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /start."""

    if is_group_update(update):
        await send_ephemeral_text(
            context.bot,
            update.effective_chat.id,
            update.effective_user.id,
            "👋 Ciao! Benvenuto nel bot!",
        )
        return

    await update.message.reply_text(
        "👋 Ciao! Benvenuto nel bot!"
    )