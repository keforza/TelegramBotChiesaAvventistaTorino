from telegram import Bot


# ============================================================
# EPHEMERAL MESSAGE UTILITIES
# ============================================================

def is_group_update(update):
    """
    Restituisce True se l'update proviene da un gruppo o supergruppo.
    """
    chat = update.effective_chat

    if not chat:
        return False

    return chat.type in ("group", "supergroup")


def get_ephemeral_message_id(message):
    """
    Recupera l'ephemeral_message_id da un messaggio Telegram.

    Supporta sia l'attributo nativo della libreria sia il valore
    eventualmente presente in api_kwargs.
    """
    if not message:
        return None

    message_id = getattr(message, "ephemeral_message_id", None)

    if message_id:
        return message_id

    api_kwargs = getattr(message, "api_kwargs", None)

    if isinstance(api_kwargs, dict):
        return api_kwargs.get("ephemeral_message_id")

    return None


def get_receiver_user_id(message, fallback_user_id=None):
    """
    Recupera l'ID dell'utente destinatario di un messaggio effimero.
    """
    if not message:
        return fallback_user_id

    receiver_user = getattr(message, "receiver_user", None)

    if receiver_user:
        receiver_id = getattr(receiver_user, "id", None)

        if receiver_id:
            return receiver_id

    api_kwargs = getattr(message, "api_kwargs", None)

    if isinstance(api_kwargs, dict):
        receiver = api_kwargs.get("receiver_user")

        if isinstance(receiver, dict):
            receiver_id = receiver.get("id")

            if receiver_id:
                return receiver_id

    return fallback_user_id


# ============================================================
# SEND
# ============================================================

async def send_text(
    bot: Bot,
    chat_id,
    user_id,
    text,
    parse_mode=None,
    reply_markup=None,
):
    """
    Invia un messaggio di testo effimero nel gruppo.

    Il messaggio sarà visibile solamente all'utente indicato
    da user_id e al bot.
    """
    api_kwargs = {
        "ephemeral_message_parameters": {
            "receiver_user_id": user_id,
        }
    }

    return await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=parse_mode,
        reply_markup=reply_markup,
        api_kwargs=api_kwargs,
    )


async def send_photo(
    bot: Bot,
    chat_id,
    user_id,
    photo,
    caption=None,
    parse_mode=None,
    reply_markup=None,
):
    """
    Invia una foto come messaggio effimero.
    """
    api_kwargs = {
        "ephemeral_message_parameters": {
            "receiver_user_id": user_id,
        }
    }

    return await bot.send_photo(
        chat_id=chat_id,
        photo=photo,
        caption=caption,
        parse_mode=parse_mode,
        reply_markup=reply_markup,
        api_kwargs=api_kwargs,
    )


# ============================================================
# EDIT
# ============================================================

async def edit_text(
    bot: Bot,
    chat_id,
    user_id,
    ephemeral_message_id,
    text,
    parse_mode=None,
    reply_markup=None,
):
    """
    Modifica il testo di un messaggio effimero esistente.
    """
    payload = {
        "chat_id": chat_id,
        "receiver_user_id": user_id,
        "ephemeral_message_id": ephemeral_message_id,
        "text": text,
    }

    if parse_mode is not None:
        payload["parse_mode"] = parse_mode

    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    return await bot.do_api_request(
        "editEphemeralMessageText",
        payload,
    )


async def edit_media(
    bot: Bot,
    chat_id,
    user_id,
    ephemeral_message_id,
    media,
    reply_markup=None,
):
    """
    Modifica il contenuto multimediale di un messaggio effimero.
    """
    payload = {
        "chat_id": chat_id,
        "receiver_user_id": user_id,
        "ephemeral_message_id": ephemeral_message_id,
        "media": media,
    }

    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    return await bot.do_api_request(
        "editEphemeralMessageMedia",
        payload,
    )


async def edit_caption(
    bot: Bot,
    chat_id,
    user_id,
    ephemeral_message_id,
    caption,
    parse_mode=None,
    reply_markup=None,
):
    """
    Modifica la caption di un messaggio effimero multimediale.
    """
    payload = {
        "chat_id": chat_id,
        "receiver_user_id": user_id,
        "ephemeral_message_id": ephemeral_message_id,
        "caption": caption,
    }

    if parse_mode is not None:
        payload["parse_mode"] = parse_mode

    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    return await bot.do_api_request(
        "editEphemeralMessageCaption",
        payload,
    )


async def edit_reply_markup(
    bot: Bot,
    chat_id,
    user_id,
    ephemeral_message_id,
    reply_markup=None,
):
    """
    Modifica solamente la tastiera inline di un messaggio effimero.
    """
    payload = {
        "chat_id": chat_id,
        "receiver_user_id": user_id,
        "ephemeral_message_id": ephemeral_message_id,
    }

    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    return await bot.do_api_request(
        "editEphemeralMessageReplyMarkup",
        payload,
    )


# ============================================================
# DELETE
# ============================================================

async def delete(
    bot: Bot,
    chat_id,
    user_id,
    ephemeral_message_id,
):
    """
    Elimina un messaggio effimero.
    """
    return await bot.do_api_request(
        "deleteEphemeralMessage",
        {
            "chat_id": chat_id,
            "receiver_user_id": user_id,
            "ephemeral_message_id": ephemeral_message_id,
        },
    )