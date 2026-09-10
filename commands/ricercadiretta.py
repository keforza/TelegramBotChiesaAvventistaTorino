import random
import re
import unicodedata

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)

from telegram.error import BadRequest

from commands.ricercaculto import (
    get_all_channel_video_ids,
    get_videos_details,
)

from ephemeral import (
    is_group_update,
    get_ephemeral_message_id,
    send_text as send_ephemeral_text,
    send_photo as send_ephemeral_photo,
    edit_text as edit_ephemeral_text,
    edit_media as edit_ephemeral_media,
    delete as delete_ephemeral_message,
)


# ============================================================
# CACHE
# ============================================================

_dirette_cache = []


def set_dirette_cache(dirette):
    """
    Imposta la cache delle dirette.
    """

    global _dirette_cache

    _dirette_cache = dirette


# ============================================================
# UTILITÀ
# ============================================================

def normalize_text(text):
    """
    Normalizza il testo per le ricerche:
    - minuscolo
    - rimozione degli accenti
    """

    if not text:
        return ""

    text = text.lower()

    text = unicodedata.normalize(
        "NFD",
        text
    )

    text = "".join(
        char
        for char in text
        if unicodedata.category(char) != "Mn"
    )

    return text


def parse_duration(duration):
    """
    Converte una durata ISO 8601 di YouTube
    in secondi.

    Esempi:
        PT38M54S -> 2334
        PT1H20M -> 4800
        PT45S -> 45
    """

    if not duration:
        return 0

    hours = 0
    minutes = 0
    seconds = 0

    match = re.match(
        r"PT"
        r"(?:(\d+)H)?"
        r"(?:(\d+)M)?"
        r"(?:(\d+)S)?",
        duration
    )

    if not match:
        return 0

    if match.group(1):
        hours = int(match.group(1))

    if match.group(2):
        minutes = int(match.group(2))

    if match.group(3):
        seconds = int(match.group(3))

    return (
        hours * 3600
        + minutes * 60
        + seconds
    )


# ============================================================
# CONTROLLO DIRETTE
# ============================================================

def is_valid_diretta(video):
    """
    Stabilisce se un video è una diretta.

    Una diretta viene riconosciuta dalla presenza
    di liveStreamingDetails.

    In questo modo:
    - dirette attive -> incluse
    - dirette terminate -> incluse
    - registrazioni di dirette -> incluse
    - video normali -> escluse
    """

    live_details = video.get(
        "liveStreamingDetails"
    )

    if not live_details:
        return False

    return True


# ============================================================
# CONVERSIONE VIDEO
# ============================================================

def convert_diretta(video):
    """
    Converte un risultato YouTube nel formato
    utilizzato dal bot.
    """

    snippet = video.get(
        "snippet",
        {}
    )

    content_details = video.get(
        "contentDetails",
        {}
    )

    live_details = video.get(
        "liveStreamingDetails",
        {}
    )

    video_id = video.get(
        "id"
    )

    title = snippet.get(
        "title",
        "Senza titolo"
    )

    description = snippet.get(
        "description",
        ""
    )

    published_at = snippet.get(
        "publishedAt"
    )

    duration = content_details.get(
        "duration",
        "PT0S"
    )

    duration_seconds = parse_duration(
        duration
    )

    thumbnails = snippet.get(
        "thumbnails",
        {}
    )

    thumbnail = ""

    if "maxres" in thumbnails:
        thumbnail = thumbnails["maxres"]["url"]

    elif "high" in thumbnails:
        thumbnail = thumbnails["high"]["url"]

    elif "medium" in thumbnails:
        thumbnail = thumbnails["medium"]["url"]

    elif "default" in thumbnails:
        thumbnail = thumbnails["default"]["url"]

    return {
        "id": video_id,
        "title": title,
        "description": description,
        "published_at": published_at,
        "duration": duration,
        "duration_seconds": duration_seconds,
        "thumbnail": thumbnail,
        "url": (
            f"https://www.youtube.com/watch?v="
            f"{video_id}"
        ),

        "actual_start_time": live_details.get(
            "actualStartTime"
        ),

        "actual_end_time": live_details.get(
            "actualEndTime"
        ),

        "scheduled_start_time": live_details.get(
            "scheduledStartTime"
        ),
    }


# ============================================================
# CARICAMENTO DIRETTE DA YOUTUBE
# ============================================================

async def load_dirette_from_youtube():
    """
    Carica tutte le dirette dal canale YouTube.

    Questa funzione viene chiamata solamente dal
    sistema di cache presente in main.py.

    I comandi Telegram NON interrogano YouTube.
    """

    video_ids = await get_all_channel_video_ids()

    videos = await get_videos_details(
        video_ids
    )

    dirette = []

    for video in videos:

        if is_valid_diretta(video):

            dirette.append(
                convert_diretta(video)
            )

    return dirette


# ============================================================
# ACCESSO CACHE
# ============================================================

def get_all_dirette():
    """
    Restituisce tutte le dirette presenti
    nella cache.
    """

    return _dirette_cache


def search_dirette(search_term):
    """
    Cerca le dirette per titolo.
    """

    search_term = normalize_text(
        search_term
    )

    results = []

    for diretta in _dirette_cache:

        title = normalize_text(
            diretta.get(
                "title",
                ""
            )
        )

        if search_term in title:

            results.append(
                diretta
            )

    return results


# ============================================================
# TASTIERA TELEGRAM
# ============================================================

def create_keyboard(
    index,
    total,
    url
):
    """
    Crea la tastiera inline.

    La paginazione viene mostrata solamente
    se ci sono più risultati.
    """

    keyboard = []

    if total > 1:

        navigation_row = [
            InlineKeyboardButton(
                "⬅️",
                callback_data="diretta_prev"
            ),

            InlineKeyboardButton(
                f"{index + 1}/{total}",
                callback_data="diretta_position"
            ),

            InlineKeyboardButton(
                "➡️",
                callback_data="diretta_next"
            ),
        ]

        keyboard.append(
            navigation_row
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "🔴 Guarda su YouTube",
                url=url
            )
        ]
    )

    return InlineKeyboardMarkup(
        keyboard
    )


# ============================================================
# DIDASCALIA
# ============================================================

def create_caption(
    index,
    total,
    diretta
):
    """
    Crea la didascalia della diretta.
    """

    title = diretta.get(
        "title",
        "Senza titolo"
    )

    duration_seconds = diretta.get(
        "duration_seconds",
        0
    )

    hours = duration_seconds // 3600

    minutes = (
        duration_seconds % 3600
    ) // 60

    seconds = (
        duration_seconds
        % 60
    )

    if hours > 0:

        duration_text = (
            f"{hours}h "
            f"{minutes:02d}m "
            f"{seconds:02d}s"
        )

    else:

        duration_text = (
            f"{minutes}m "
            f"{seconds:02d}s"
        )

    if total > 1:

        return (
            f"🔴 <b>{title}</b>\n\n"
            f"📺 Diretta {index + 1}/{total}\n"
            f"⏱️ Durata: {duration_text}"
        )

    return (
        f"🔴 <b>{title}</b>\n\n"
        f"⏱️ Durata: {duration_text}"
    )


# ============================================================
# INVIO DIRETTA
# ============================================================

async def send_diretta(
    bot,
    chat_id,
    diretta,
    index,
    total,
    ephemeral=False,
    user_id=None,
):
    """
    Invia la diretta come nuovo messaggio.

    In gruppo:
        usa Ephemeral Messages.

    In chat privata:
        usa i normali messaggi Telegram.
    """

    url = diretta.get(
        "url",
        ""
    )

    thumbnail = diretta.get(
        "thumbnail",
        ""
    )

    caption = create_caption(
        index,
        total,
        diretta
    )

    keyboard = create_keyboard(
        index,
        total,
        url
    )

    # ========================================================
    # MESSAGGIO EFFIMERO
    # ========================================================

    if ephemeral:

        if not user_id:
            raise ValueError(
                "user_id è obbligatorio "
                "per un messaggio effimero."
            )

        if thumbnail:

            return await send_ephemeral_photo(
                bot,
                chat_id,
                user_id,
                thumbnail,
                caption,
                "HTML",
                keyboard,
            )

        return await send_ephemeral_text(
            bot,
            chat_id,
            user_id,
            caption,
            "HTML",
            keyboard,
        )

    # ========================================================
    # MESSAGGIO NORMALE
    # ========================================================

    if thumbnail:

        return await bot.send_photo(
            chat_id=chat_id,
            photo=thumbnail,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    return await bot.send_message(
        chat_id=chat_id,
        text=caption,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ============================================================
# COMANDO /DIRETTA
# ============================================================

async def ricercadiretta(
    update,
    context
):
    """
    Gestisce:

        /diretta

    oppure:

        /diretta parola

    Nei gruppi:
        il risultato viene inviato come
        messaggio effimero privato.
    """

    search_term = " ".join(
        context.args
    ).strip()

    # ========================================================
    # EPHEMERAL
    # ========================================================

    ephemeral = is_group_update(
        update
    )

    user_id = (
        update.effective_user.id
        if update.effective_user
        else None
    )

    chat_id = (
        update.effective_chat.id
        if update.effective_chat
        else None
    )

    bot = context.bot

    # --------------------------------------------------------
    # /diretta senza ricerca
    # --------------------------------------------------------

    if not search_term:

        dirette = get_all_dirette()

        if not dirette:

            text = (
                "❌ Non ci sono dirette "
                "disponibili nella cache."
            )

            if ephemeral:

                await send_ephemeral_text(
                    bot,
                    chat_id,
                    user_id,
                    text,
                )

            else:

                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                )

            return

        diretta = random.choice(
            dirette
        )

        results = [
            diretta
        ]

    # --------------------------------------------------------
    # /diretta parola
    # --------------------------------------------------------

    else:

        results = search_dirette(
            search_term
        )

        if not results:

            text = (
                "❌ Nessuna diretta trovata "
                f"per: <b>{search_term}</b>"
            )

            if ephemeral:

                await send_ephemeral_text(
                    bot,
                    chat_id,
                    user_id,
                    text,
                    "HTML",
                )

            else:

                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="HTML"
                )

            return

    # --------------------------------------------------------
    # Salva risultati per la paginazione
    # --------------------------------------------------------

    context.user_data[
        "diretta_results"
    ] = results

    context.user_data[
        "diretta_index"
    ] = 0

    # --------------------------------------------------------
    # Invia risultato
    # --------------------------------------------------------

    await send_diretta(
        bot,
        chat_id,
        results[0],
        0,
        len(results),
        ephemeral=ephemeral,
        user_id=user_id,
    )


# ============================================================
# NAVIGAZIONE
# ============================================================

async def diretta_navigation(
    update,
    context
):
    """
    Gestisce i pulsanti:

        diretta_prev
        diretta_next
        diretta_position

    Se il messaggio è effimero, tutte le operazioni
    vengono gestite tramite ephemeral.py.
    """

    query = update.callback_query

    await query.answer()

    results = context.user_data.get(
        "diretta_results",
        []
    )

    if not results:
        return

    index = context.user_data.get(
        "diretta_index",
        0
    )

    total = len(results)

    # ========================================================
    # PRECEDENTE
    # ========================================================

    if query.data == "diretta_prev":

        index -= 1

        if index < 0:
            index = total - 1

    # ========================================================
    # SUCCESSIVO
    # ========================================================

    elif query.data == "diretta_next":

        index += 1

        if index >= total:
            index = 0

    # ========================================================
    # POSIZIONE
    # ========================================================

    elif query.data == "diretta_position":

        return

    else:

        return

    # --------------------------------------------------------
    # Aggiorna indice
    # --------------------------------------------------------

    context.user_data[
        "diretta_index"
    ] = index

    diretta = results[index]

    url = diretta.get(
        "url",
        ""
    )

    thumbnail = diretta.get(
        "thumbnail",
        ""
    )

    caption = create_caption(
        index,
        total,
        diretta
    )

    keyboard = create_keyboard(
        index,
        total,
        url
    )

    message = query.message

    # ========================================================
    # IDENTIFICA MESSAGGIO EFFIMERO
    # ========================================================

    ephemeral_message_id = (
        get_ephemeral_message_id(
            message
        )
    )

    is_ephemeral = (
        ephemeral_message_id is not None
    )

    user_id = (
        update.effective_user.id
        if update.effective_user
        else None
    )

    chat_id = (
        message.chat_id
        if message
        else update.effective_chat.id
    )

    # ========================================================
    # MESSAGGIO EFFIMERO
    # ========================================================

    if is_ephemeral:

        has_photo = bool(
            message.photo
        )

        new_has_photo = bool(
            thumbnail
        )

        try:

            # ------------------------------------------------
            # FOTO -> FOTO
            # ------------------------------------------------

            if has_photo and new_has_photo:

                await edit_ephemeral_media(
                    context.bot,
                    chat_id,
                    user_id,
                    ephemeral_message_id,
                    InputMediaPhoto(
                        media=thumbnail,
                        caption=caption,
                        parse_mode="HTML"
                    ),
                    keyboard
                )

            # ------------------------------------------------
            # TESTO -> TESTO
            # ------------------------------------------------

            elif (
                not has_photo
                and not new_has_photo
            ):

                await edit_ephemeral_text(
                    context.bot,
                    chat_id,
                    user_id,
                    ephemeral_message_id,
                    caption,
                    "HTML",
                    keyboard
                )

            # ------------------------------------------------
            # FOTO -> TESTO
            # ------------------------------------------------

            elif has_photo and not new_has_photo:

                await delete_ephemeral_message(
                    context.bot,
                    chat_id,
                    user_id,
                    ephemeral_message_id
                )

                await send_ephemeral_text(
                    context.bot,
                    chat_id,
                    user_id,
                    caption,
                    "HTML",
                    keyboard
                )

            # ------------------------------------------------
            # TESTO -> FOTO
            # ------------------------------------------------

            elif (
                not has_photo
                and new_has_photo
            ):

                await delete_ephemeral_message(
                    context.bot,
                    chat_id,
                    user_id,
                    ephemeral_message_id
                )

                await send_ephemeral_photo(
                    context.bot,
                    chat_id,
                    user_id,
                    thumbnail,
                    caption,
                    "HTML",
                    keyboard
                )

        except BadRequest:

            pass

        return

    # ========================================================
    # MESSAGGIO NORMALE
    # ========================================================

    # ========================================================
    # FOTO -> FOTO
    # ========================================================

    if message.photo and thumbnail:

        try:

            await message.edit_media(
                media=InputMediaPhoto(
                    media=thumbnail,
                    caption=caption,
                    parse_mode="HTML"
                ),
                reply_markup=keyboard
            )

        except BadRequest:

            pass

        return

    # ========================================================
    # TESTO -> TESTO
    # ========================================================

    if not message.photo and not thumbnail:

        try:

            await message.edit_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=keyboard
            )

        except BadRequest:

            pass

        return

    # ========================================================
    # FOTO -> TESTO
    # ========================================================

    if message.photo and not thumbnail:

        try:

            await message.delete()

        except BadRequest:

            pass

        await context.bot.send_message(
            chat_id=chat_id,
            text=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )

        return

    # ========================================================
    # TESTO -> FOTO
    # ========================================================

    if not message.photo and thumbnail:

        try:

            await message.delete()

        except BadRequest:

            pass

        await context.bot.send_photo(
            chat_id=chat_id,
            photo=thumbnail,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )

        return