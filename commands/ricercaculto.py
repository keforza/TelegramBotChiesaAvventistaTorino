import os
import random
import re
import unicodedata

import aiohttp

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)

from telegram.error import BadRequest

from ephemeral import (
    is_group_update,
    get_ephemeral_message_id,
    send_text as send_ephemeral_text,
    send_photo as send_ephemeral_photo,
    edit_text as edit_ephemeral_text,
    edit_media as edit_ephemeral_media,
    delete as delete_ephemeral_message,
)


# ==================================================
# CACHE
# ==================================================

_culti_cache = []


def set_culti_cache(culti):
    """
    Aggiorna la cache dei culti.
    Viene chiamata dal main.py quando aggiorna
    i dati da YouTube.
    """

    global _culti_cache

    _culti_cache = list(culti)


# ==================================================
# CONFIGURAZIONE YOUTUBE
# ==================================================

def get_youtube_config():
    api_key = os.getenv("YOUTUBE_API_KEY")
    channel_id = os.getenv("YOUTUBE_CHANNEL_ID")

    if not api_key:
        raise RuntimeError(
            "YOUTUBE_API_KEY non trovato nel file .env"
        )

    if not channel_id:
        raise RuntimeError(
            "YOUTUBE_CHANNEL_ID non trovato nel file .env"
        )

    return api_key, channel_id


# ==================================================
# NORMALIZZAZIONE TESTO
# ==================================================

def normalize_text(text):
    """
    Rimuove gli accenti e rende il testo
    confrontabile senza distinzione tra
    maiuscole e minuscole.
    """

    text = unicodedata.normalize(
        "NFD",
        text,
    )

    text = "".join(
        char
        for char in text
        if unicodedata.category(char) != "Mn"
    )

    return text.casefold().strip()


# ==================================================
# PARSING DURATA
# ==================================================

def parse_duration(duration):
    """
    Converte una durata ISO 8601 di YouTube
    in secondi.
    """

    match = re.fullmatch(
        r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
        duration,
    )

    if not match:
        return 0

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return (
        hours * 3600
        + minutes * 60
        + seconds
    )


# ==================================================
# RICHIESTA API YOUTUBE
# ==================================================

async def youtube_get(endpoint, params):
    """
    Effettua una richiesta GET alle API YouTube.

    Questa funzione viene utilizzata solamente
    durante l'aggiornamento della cache.
    """

    api_key, _ = get_youtube_config()

    params = dict(params)
    params["key"] = api_key

    url = (
        "https://www.googleapis.com/"
        f"youtube/v3/{endpoint}"
    )

    async with aiohttp.ClientSession() as session:

        async with session.get(
            url,
            params=params,
        ) as response:

            if response.status != 200:

                text = await response.text()

                raise RuntimeError(
                    "Errore API YouTube "
                    f"({response.status}): {text}"
                )

            return await response.json()


# ==================================================
# OTTIENI TUTTI GLI ID DEI VIDEO DEL CANALE
# ==================================================

async def get_all_channel_video_ids():
    """
    Recupera tutti gli ID dei video presenti
    nella playlist Uploads del canale.
    """

    _, channel_id = get_youtube_config()

    channel_data = await youtube_get(
        "channels",
        {
            "part": "contentDetails",
            "id": channel_id,
        },
    )

    items = channel_data.get(
        "items",
        [],
    )

    if not items:
        raise RuntimeError(
            "Canale YouTube non trovato."
        )

    uploads_playlist_id = (
        items[0]
        .get("contentDetails", {})
        .get("relatedPlaylists", {})
        .get("uploads")
    )

    if not uploads_playlist_id:
        raise RuntimeError(
            "Playlist Uploads non trovata."
        )

    video_ids = []

    next_page_token = None

    while True:

        params = {
            "part": "contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": 50,
        }

        if next_page_token:
            params["pageToken"] = next_page_token

        data = await youtube_get(
            "playlistItems",
            params,
        )

        for item in data.get(
            "items",
            [],
        ):

            video_id = (
                item
                .get("contentDetails", {})
                .get("videoId")
            )

            if video_id:
                video_ids.append(video_id)

        next_page_token = data.get(
            "nextPageToken"
        )

        if not next_page_token:
            break

    return video_ids


# ==================================================
# DETTAGLI VIDEO
# ==================================================

async def get_videos_details(video_ids):
    """
    Recupera i dettagli dei video a blocchi
    di massimo 50 ID per richiesta.
    """

    videos = []

    for start in range(
        0,
        len(video_ids),
        50,
    ):

        batch = video_ids[
            start:start + 50
        ]

        data = await youtube_get(
            "videos",
            {
                "part": (
                    "snippet,"
                    "contentDetails,"
                    "liveStreamingDetails"
                ),
                "id": ",".join(batch),
            },
        )

        videos.extend(
            data.get(
                "items",
                []
            )
        )

    return videos


# ==================================================
# CONTROLLO VIDEO VALIDO
# ==================================================

def is_valid_culto(video):
    """
    Accetta solamente normali video YouTube.

    Esclude:
    - live attualmente in corso
    - live terminate
    - registrazioni di live
    - premiere/broadcast
    - video di durata <= 10 minuti
    """

    # --------------------------------------------------
    # ESCLUDI LIVE E REGISTRAZIONI DI LIVE
    # --------------------------------------------------

    if video.get("liveStreamingDetails"):
        return False

    # --------------------------------------------------
    # ESCLUDI PREMIERE / BROADCAST
    # --------------------------------------------------

    snippet = video.get(
        "snippet",
        {},
    )

    if snippet.get(
        "liveBroadcastContent"
    ) != "none":

        return False

    # --------------------------------------------------
    # CONTROLLO DURATA
    # --------------------------------------------------

    content_details = video.get(
        "contentDetails",
        {},
    )

    duration = content_details.get(
        "duration"
    )

    if not duration:
        return False

    duration_seconds = parse_duration(
        duration
    )

    # Deve essere STRICTLY maggiore di 10 minuti.
    # Quindi 10:00 viene escluso.

    if duration_seconds <= 600:
        return False

    return True


# ==================================================
# CONVERSIONE VIDEO
# ==================================================

def convert_video(video):
    """
    Converte la risposta YouTube nel formato
    utilizzato dal bot.
    """

    video_id = video.get(
        "id"
    )

    snippet = video.get(
        "snippet",
        {},
    )

    content_details = video.get(
        "contentDetails",
        {},
    )

    title = snippet.get(
        "title",
        "Senza titolo",
    )

    description = snippet.get(
        "description",
        "",
    )

    published_at = snippet.get(
        "publishedAt",
        "",
    )

    duration = content_details.get(
        "duration",
        "PT0S",
    )

    thumbnails = snippet.get(
        "thumbnails",
        {},
    )

    thumbnail = None

    for key in (
        "maxres",
        "high",
        "medium",
        "default",
    ):

        if key in thumbnails:

            thumbnail = thumbnails[key].get(
                "url"
            )

            if thumbnail:
                break

    return {
        "id": video_id,
        "title": title,
        "description": description,
        "published_at": published_at,
        "duration": duration,
        "duration_seconds": parse_duration(
            duration
        ),
        "thumbnail": thumbnail,
        "url": (
            "https://www.youtube.com/watch?v="
            f"{video_id}"
        ),
    }


# ==================================================
# CARICAMENTO DATI DA YOUTUBE
# ==================================================

async def load_culti_from_youtube():
    """
    Interroga YouTube e costruisce la lista
    dei culti validi.

    IMPORTANTE:
    questa funzione viene chiamata solamente
    dal main.py per aggiornare la cache.

    I comandi Telegram NON chiamano direttamente
    questa funzione.
    """

    video_ids = (
        await get_all_channel_video_ids()
    )

    videos = await get_videos_details(
        video_ids
    )

    culti = []

    for video in videos:

        if is_valid_culto(video):

            culti.append(
                convert_video(video)
            )

    return culti


# ==================================================
# OTTIENI TUTTI I CULTI DALLA CACHE
# ==================================================

def get_all_culti():
    """
    Restituisce tutti i culti presenti
    nella cache.

    NON interroga YouTube.
    """

    return list(
        _culti_cache
    )


# ==================================================
# CERCA CULTI NELLA CACHE
# ==================================================

def search_culti(search_term):
    """
    Cerca un culto solamente nella cache.

    NON interroga YouTube.
    """

    normalized_search = normalize_text(
        search_term
    )

    results = []

    for video in _culti_cache:

        title = video.get(
            "title",
            "",
        )

        normalized_title = normalize_text(
            title
        )

        if normalized_search not in normalized_title:
            continue

        results.append(
            video
        )

    return results


# ==================================================
# CREAZIONE TASTIERA
# ==================================================

def create_keyboard(
    index,
    total,
    url,
):
    """
    Crea i pulsanti per la navigazione
    tra i risultati.

    La paginazione viene mostrata solamente
    quando ci sono almeno 2 risultati.
    """

    keyboard = []

    # ==================================================
    # PAGINAZIONE
    # ==================================================

    if total > 1:

        buttons = []

        # --------------------------------------------------
        # PRECEDENTE
        # --------------------------------------------------

        if index > 0:

            buttons.append(
                InlineKeyboardButton(
                    "⬅️",
                    callback_data="culto_prev",
                )
            )

        # --------------------------------------------------
        # POSIZIONE
        # --------------------------------------------------

        buttons.append(
            InlineKeyboardButton(
                f"{index + 1}/{total}",
                callback_data="culto_position",
            )
        )

        # --------------------------------------------------
        # SUCCESSIVO
        # --------------------------------------------------

        if index < total - 1:

            buttons.append(
                InlineKeyboardButton(
                    "➡️",
                    callback_data="culto_next",
                )
            )

        keyboard.append(
            buttons
        )

    # ==================================================
    # YOUTUBE
    # ==================================================

    keyboard.append(
        [
            InlineKeyboardButton(
                "▶️ Guarda su YouTube",
                url=url,
            )
        ]
    )

    return InlineKeyboardMarkup(
        keyboard
    )


# ==================================================
# CREAZIONE CAPTION
# ==================================================

def create_caption(
    culto,
    index,
    total,
):
    """
    Crea il testo mostrato sotto il culto.
    """

    title = culto.get(
        "title",
        "Senza titolo",
    )

    duration_seconds = culto.get(
        "duration_seconds",
        0,
    )

    minutes = duration_seconds // 60
    seconds = duration_seconds % 60

    duration_text = (
        f"{minutes}:{seconds:02d}"
    )

    # --------------------------------------------------
    # UN SOLO RISULTATO
    # --------------------------------------------------

    if total == 1:

        return (
            f"⛪ <b>{title}</b>\n\n"
            f"⏱ Durata: {duration_text}"
        )

    # --------------------------------------------------
    # PIÙ RISULTATI
    # --------------------------------------------------

    return (
        f"⛪ <b>{title}</b>\n\n"
        f"⏱ Durata: {duration_text}\n"
        f"📺 Risultato {index + 1}/{total}"
    )


# ==================================================
# INVIO CULTO
# ==================================================

async def send_culto(
    target,
    culto,
    index,
    total,
    ephemeral=False,
    user_id=None,
    chat_id=None,
):
    """
    Invia il culto come NUOVO MESSAGGIO.

    In chat privata:
        usa il normale sistema Telegram.

    In gruppo/supergruppo:
        usa il sistema Ephemeral Messages.
    """

    caption = create_caption(
        culto,
        index,
        total,
    )

    keyboard = create_keyboard(
        index,
        total,
        culto["url"],
    )

    thumbnail = culto.get(
        "thumbnail"
    )

    # ==================================================
    # MESSAGGIO EFFIMERO
    # ==================================================

    if ephemeral:

        if not user_id or chat_id is None:
            raise ValueError(
                "user_id e chat_id sono obbligatori "
                "per un messaggio effimero."
            )

        if thumbnail:

            return await send_ephemeral_photo(
                target,
                chat_id,
                user_id,
                thumbnail,
                caption,
                "HTML",
                keyboard,
            )

        return await send_ephemeral_text(
            target,
            chat_id,
            user_id,
            caption,
            "HTML",
            keyboard,
        )

    # ==================================================
    # MESSAGGIO NORMALE
    # ==================================================

    if thumbnail:

        return await target.reply_photo(
            photo=thumbnail,
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    return await target.reply_text(
        text=caption,
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# ==================================================
# COMANDO /CULTO
# ==================================================

async def ricercaculto(
    update,
    context,
):
    """
    /culto
        Mostra un culto casuale dalla cache.
        NESSUNA PAGINAZIONE.

    /culto parola
        Cerca i culti nella cache.
        La paginazione appare solamente
        se ci sono più risultati.

    Nei gruppi:
        comando e risultati sono effimeri
        e visibili solamente all'utente.
    """

    search_term = ""

    if context.args:

        search_term = " ".join(
            context.args
        ).strip()

    # ==================================================
    # DETERMINA SE SIAMO IN UN GRUPPO
    # ==================================================

    ephemeral = is_group_update(update)

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

    # ==================================================
    # CACHE NON ANCORA PRONTA
    # ==================================================

    if not _culti_cache:

        if ephemeral:

            await send_ephemeral_text(
                bot,
                chat_id,
                user_id,
                "⏳ La cache dei culti non è ancora "
                "pronta. Riprova tra qualche secondo.",
            )

        else:

            await update.message.reply_text(
                "⏳ La cache dei culti non è ancora "
                "pronta. Riprova tra qualche secondo."
            )

        return

    # ==================================================
    # /CULTO
    # ==================================================

    if not search_term:

        all_culti = get_all_culti()

        if not all_culti:

            if ephemeral:

                await send_ephemeral_text(
                    bot,
                    chat_id,
                    user_id,
                    "❌ Non ho trovato nessun culto valido.",
                )

            else:

                await update.message.reply_text(
                    "❌ Non ho trovato nessun culto valido."
                )

            return

        culto = random.choice(
            all_culti
        )

        await send_culto(
            bot if ephemeral else update.message,
            culto,
            0,
            1,
            ephemeral=ephemeral,
            user_id=user_id,
            chat_id=chat_id,
        )

        return

    # ==================================================
    # /CULTO + RICERCA
    # ==================================================

    results = search_culti(
        search_term
    )

    if not results:

        text = (
            "❌ Nessun culto trovato "
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

            await update.message.reply_text(
                text,
                parse_mode="HTML",
            )

        return

    # --------------------------------------------------
    # SALVA RISULTATI PER PAGINAZIONE
    # --------------------------------------------------

    context.user_data[
        "culto_results"
    ] = results

    context.user_data[
        "culto_index"
    ] = 0

    index = 0

    culto = results[index]

    total = len(results)

    await send_culto(
        bot if ephemeral else update.message,
        culto,
        index,
        total,
        ephemeral=ephemeral,
        user_id=user_id,
        chat_id=chat_id,
    )


# ==================================================
# NAVIGAZIONE PAGINAZIONE
# ==================================================

async def culto_navigation(
    update,
    context,
):
    """
    Gestisce i pulsanti precedente/successivo.

    Se il messaggio è effimero, tutte le modifiche
    vengono effettuate tramite ephemeral.py.
    """

    query = update.callback_query

    await query.answer()

    results = context.user_data.get(
        "culto_results",
        [],
    )

    # ==================================================
    # DATI NON PIÙ DISPONIBILI
    # ==================================================

    if not results:

        ephemeral_message_id = (
            get_ephemeral_message_id(
                query.message
            )
        )

        if ephemeral_message_id:

            try:

                await edit_ephemeral_text(
                    context.bot,
                    query.message.chat_id,
                    update.effective_user.id,
                    ephemeral_message_id,
                    "La ricerca non è più disponibile. "
                    "Rifai il comando.",
                )

            except BadRequest:
                pass

        else:

            try:

                await query.edit_message_text(
                    "La ricerca non è più disponibile. "
                    "Rifai il comando."
                )

            except BadRequest:
                pass

        return

    # ==================================================
    # IDENTIFICA MESSAGGIO EFFIMERO
    # ==================================================

    ephemeral_message_id = (
        get_ephemeral_message_id(
            query.message
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
        query.message.chat_id
        if query.message
        else update.effective_chat.id
    )

    # ==================================================
    # INDICE ATTUALE
    # ==================================================

    current_index = context.user_data.get(
        "culto_index",
        0,
    )

    total = len(results)

    # ==================================================
    # PULSANTE POSIZIONE
    # ==================================================

    if query.data == "culto_position":

        return

    # ==================================================
    # PRECEDENTE
    # ==================================================

    if query.data == "culto_prev":

        if current_index <= 0:
            return

        new_index = (
            current_index - 1
        )

    # ==================================================
    # SUCCESSIVO
    # ==================================================

    elif query.data == "culto_next":

        if current_index >= total - 1:
            return

        new_index = (
            current_index + 1
        )

    else:

        return

    # ==================================================
    # AGGIORNA INDICE
    # ==================================================

    context.user_data[
        "culto_index"
    ] = new_index

    culto = results[new_index]

    caption = create_caption(
        culto,
        new_index,
        total,
    )

    keyboard = create_keyboard(
        new_index,
        total,
        culto["url"],
    )

    # ==================================================
    # MESSAGGIO EFFIMERO
    # ==================================================

    if is_ephemeral:

        has_photo = bool(
            query.message.photo
        )

        new_has_photo = bool(
            culto.get("thumbnail")
        )

        try:

            # --------------------------------------------------
            # FOTO -> FOTO
            # --------------------------------------------------

            if has_photo and new_has_photo:

                await edit_ephemeral_media(
                    context.bot,
                    chat_id,
                    user_id,
                    ephemeral_message_id,
                    InputMediaPhoto(
                        media=culto["thumbnail"],
                        caption=caption,
                        parse_mode="HTML",
                    ),
                    keyboard,
                )

            # --------------------------------------------------
            # TESTO -> TESTO
            # --------------------------------------------------

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
                    keyboard,
                )

            # --------------------------------------------------
            # FOTO -> TESTO
            # --------------------------------------------------

            elif has_photo and not new_has_photo:

                await delete_ephemeral_message(
                    context.bot,
                    chat_id,
                    user_id,
                    ephemeral_message_id,
                )

                await send_ephemeral_text(
                    context.bot,
                    chat_id,
                    user_id,
                    caption,
                    "HTML",
                    keyboard,
                )

            # --------------------------------------------------
            # TESTO -> FOTO
            # --------------------------------------------------

            elif (
                not has_photo
                and new_has_photo
            ):

                await delete_ephemeral_message(
                    context.bot,
                    chat_id,
                    user_id,
                    ephemeral_message_id,
                )

                await send_ephemeral_photo(
                    context.bot,
                    chat_id,
                    user_id,
                    culto["thumbnail"],
                    caption,
                    "HTML",
                    keyboard,
                )

        except BadRequest:
            pass

        return

    # ==================================================
    # MESSAGGIO NORMALE
    # ==================================================

    has_photo = bool(
        query.message.photo
    )

    new_has_photo = bool(
        culto.get("thumbnail")
    )

    try:

        # --------------------------------------------------
        # FOTO -> FOTO
        # --------------------------------------------------

        if has_photo and new_has_photo:

            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=culto["thumbnail"],
                    caption=caption,
                    parse_mode="HTML",
                ),
                reply_markup=keyboard,
            )

        # --------------------------------------------------
        # TESTO -> TESTO
        # --------------------------------------------------

        elif (
            not has_photo
            and not new_has_photo
        ):

            await query.edit_message_text(
                text=caption,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        # --------------------------------------------------
        # FOTO -> TESTO
        # --------------------------------------------------

        elif has_photo and not new_has_photo:

            await query.message.delete()

            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=caption,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        # --------------------------------------------------
        # TESTO -> FOTO
        # --------------------------------------------------

        elif (
            not has_photo
            and new_has_photo
        ):

            await query.message.delete()

            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=culto["thumbnail"],
                caption=caption,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

    except BadRequest:
        pass