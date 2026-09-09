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


def parse_duration(duration):
    """Converte una durata YouTube ISO 8601 in secondi."""

    match = re.fullmatch(
        r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
        duration,
    )

    if not match:
        return None

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds


async def search_culti(query, max_results=10):
    """Cerca culti sul canale YouTube configurato."""

    if not YOUTUBE_API_KEY:
        logger.error(
            "YOUTUBE_API_KEY non configurata nel file .env"
        )
        return []

    if not CHANNEL_ID:
        logger.error(
            "CHANNEL_ID non configurata nel file .env"
        )
        return []

    search_url = (
        "https://www.googleapis.com/youtube/v3/search"
    )

    search_params = {
        "part": "snippet",
        "channelId": CHANNEL_ID,
        "type": "video",
        "q": query,
        "order": "relevance",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
    }

    try:
        async with aiohttp.ClientSession() as session:

            # Ricerca dei video
            async with session.get(
                search_url,
                params=search_params,
            ) as response:

                response.raise_for_status()
                search_data = await response.json()

            items = search_data.get("items", [])

            if not items:
                logger.info(
                    "Nessun video trovato per: %s",
                    query,
                )
                return []

            video_ids = [
                item["id"]["videoId"]
                for item in items
                if item.get("id", {}).get("videoId")
            ]

            if not video_ids:
                return []

            # Recuperiamo durata e informazioni aggiuntive
            videos_url = (
                "https://www.googleapis.com/youtube/v3/videos"
            )

            videos_params = {
                "part": (
                    "contentDetails,"
                    "liveStreamingDetails,"
                    "snippet"
                ),
                "id": ",".join(video_ids),
                "key": YOUTUBE_API_KEY,
            }

            async with session.get(
                videos_url,
                params=videos_params,
            ) as response:

                response.raise_for_status()
                videos_data = await response.json()

        videos_by_id = {
            video["id"]: video
            for video in videos_data.get("items", [])
        }

        results = []

        for item in items:

            video_id = item["id"]["videoId"]
            video = videos_by_id.get(video_id)

            if not video:
                continue

            title = video["snippet"]["title"]

            # Ignora le live
            if "liveStreamingDetails" in video:
                logger.info(
                    "Ignoro live: %s",
                    title,
                )
                continue

            duration = video["contentDetails"].get(
                "duration"
            )

            total_seconds = parse_duration(duration)

            if total_seconds is None:
                logger.warning(
                    "Durata non riconosciuta per %s: %s",
                    title,
                    duration,
                )
                continue

            # Ignora video di 3 minuti o meno
            if total_seconds <= 180:
                logger.info(
                    "Ignoro video troppo corto: %s (%s secondi)",
                    title,
                    total_seconds,
                )
                continue

            video_url = (
                f"https://www.youtube.com/watch?v={video_id}"
            )

            results.append(
                {
                    "title": title,
                    "url": video_url,
                    "published_at": video["snippet"].get(
                        "publishedAt"
                    ),
                    "duration": total_seconds,
                }
            )

        logger.info(
            "Ricerca '%s': trovati %d culti validi.",
            query,
            len(results),
        )

        return results

    except ClientError as e:
        logger.error(
            "Errore nella richiesta all'API YouTube: %s",
            e,
        )
        return []

    except (KeyError, TypeError, ValueError) as e:
        logger.error(
            "Risposta YouTube non valida: %s",
            e,
        )
        return []

    except Exception as e:
        logger.exception(
            "Errore imprevisto durante la ricerca YouTube: %s",
            e,
        )
        return []


async def ricercaculto(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Gestisce il comando /ricercaculto."""

    if not context.args:

        if update.message:
            await update.message.reply_text(
                "⚠️ Devi specificare cosa vuoi cercare.\n\n"
                "Esempio:\n"
                "/ricercaculto pazienza"
            )

        return

    query = " ".join(context.args).strip()

    logger.info(
        "Ricerca culto richiesta: %s",
        query,
    )

    results = await search_culti(query)

    if not update.message:
        return

    if not results:

        await update.message.reply_text(
            f"❌ Non ho trovato culti per: {query}"
        )

        return

    message_lines = [
        f"🔎 Risultati per: {query}",
        "",
    ]

    for index, result in enumerate(
        results,
        start=1,
    ):

        message_lines.append(
            f"{index}. {result['title']}\n"
            f"🎥 {result['url']}\n"
        )

    await update.message.reply_text(
        "\n".join(message_lines)
    )