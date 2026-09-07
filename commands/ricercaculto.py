from telegram import Update
from telegram.ext import ContextTypes
from aiohttp import ClientError
from dotenv import load_dotenv

import aiohttp
import logging
import os
import re


load_dotenv(".env")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")

logger = logging.getLogger(__name__)


async def get_latest_video(predicatore):
    """Recupera l'ultimo video lungo non-live del predicatore."""

    if not YOUTUBE_API_KEY:
        logger.error("YOUTUBE_API_KEY non configurata nel file .env")
        return None, None

    if not CHANNEL_ID:
        logger.error("CHANNEL_ID non configurata nel file .env")
        return None, None

    search_url = (
        "https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet"
        f"&channelId={CHANNEL_ID}"
        f"&type=video"
        f"&order=date"
        f"&maxResults=20"
        f"&key={YOUTUBE_API_KEY}"
    )

    try:
        async with aiohttp.ClientSession() as session:

            async with session.get(search_url) as response:
                response.raise_for_status()
                search_data = await response.json()

            items = search_data.get("items", [])

            if not items:
                logger.info("Nessun video trovato.")
                return None, None

            video_ids = [
                item["id"]["videoId"]
                for item in items
                if item.get("id", {}).get("videoId")
            ]

            if not video_ids:
                logger.info("Nessun ID video trovato.")
                return None, None

            videos_url = (
                "https://www.googleapis.com/youtube/v3/videos"
                f"?part=contentDetails,liveStreamingDetails,snippet"
                f"&id={','.join(video_ids)}"
                f"&key={YOUTUBE_API_KEY}"
            )

            async with session.get(videos_url) as response:
                response.raise_for_status()
                videos_data = await response.json()

        # I video arrivano nello stesso ordine della ricerca?
        # Per sicurezza li rimettiamo nell'ordine originale.
        videos_by_id = {
            video["id"]: video
            for video in videos_data.get("items", [])
        }

        for item in items:

            video_id = item["id"]["videoId"]
            video = videos_by_id.get(video_id)

            if not video:
                continue

            video_title = video["snippet"]["title"]

            # Controlliamo il nome del predicatore nel titolo.
            if predicatore.lower() not in video_title.lower():
                continue

            # Escludiamo le live.
            if "liveStreamingDetails" in video:
                logger.info(
                    "Ignoro live: %s",
                    video_title
                )
                continue

            duration = video["contentDetails"]["duration"]

            # Durata ISO 8601.
            match = re.fullmatch(
                r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
                duration
            )

            if not match:
                logger.warning(
                    "Durata non riconosciuta per %s: %s",
                    video_title,
                    duration
                )
                continue

            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)

            total_seconds = (
                hours * 3600
                + minutes * 60
                + seconds
            )

            # Deve essere superiore a 3 minuti.
            if total_seconds <= 180:
                logger.info(
                    "Ignoro video troppo corto: %s (%s secondi)",
                    video_title,
                    total_seconds
                )
                continue

            video_url = (
                f"https://www.youtube.com/watch?v={video_id}"
            )

            logger.info(
                "Ultimo video trovato per %s: %s",
                predicatore,
                video_title
            )

            return video_title, video_url

        logger.info(
            "Nessun video lungo non-live trovato per %s.",
            predicatore
        )

        return None, None

    except ClientError as e:
        logger.error(
            "Errore nella richiesta all'API YouTube: %s",
            e
        )
        return None, None

    except (KeyError, TypeError, ValueError) as e:
        logger.error(
            "Risposta YouTube non valida: %s",
            e
        )
        return None, None

    except Exception as e:
        logger.exception(
            "Errore imprevisto durante il recupero del video: %s",
            e
        )
        return None, None


async def handle_ultimovideo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Gestisce il comando /culto."""

    if not context.args:
        if update.message:
            await update.message.reply_text(
                "⚠️ Devi specificare il nome del predicatore.\n\n"
                "Esempio:\n"
                "/culto Mario Rossi"
            )
        return

    predicatore = " ".join(context.args).strip()

    title, url = await get_latest_video(predicatore)

    if title and url:
        message = (
            f"🎥 Ultimo culto di {predicatore}:\n"
            f"{title}\n\n"
            f"🔴 Guarda qui: {url}"
        )
    else:
        message = (
            f"❌ Non ho trovato un video recente di "
            f"{predicatore} che soddisfi i requisiti."
        )

    if update.message:
        await update.message.reply_text(message)