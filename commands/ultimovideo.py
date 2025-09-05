from telegram import Update
from telegram.ext import ContextTypes
from aiohttp import ClientError
import logging
import os

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")

logger = logging.getLogger(__name__)

async def get_latest_video():
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={CHANNEL_ID}&type=video&order=date&key={YOUTUBE_API_KEY}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

        if "items" in data and data["items"]:
            video_id = data["items"][0]["id"]["videoId"]
            video_title = data["items"][0]["snippet"]["title"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            return video_title, video_url
        return None, None
    except ClientError as e:
        logger.error(f"Errore API YouTube: {e}")
        return None, None

async def handle_ultimovideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title, url = await get_latest_video()
    if title and url:
        message = f"🎥 Ultimo video: {title}\n🔴 Guarda qui: {url}"
    else:
        message = "Nessun video recente trovato."
    await update.message.reply_text(message)