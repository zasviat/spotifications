from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

import json
import os
from dotenv import load_dotenv
import requests

from src.proxy import get_spotify_proxy
from src.clients.spotipy_client import SpotipyClient
from src.models import NotificationKeyboardButton
from src.clients.telegram_client import TelegramClient
from src.constants import (
    MAIN_PLAYLIST_ID,
    SPOTIFICATIONS_PLAYLIST_LINK,
    SPOTIFICATIONS_PLAYLIST_ID,
)
from loguru import logger


load_dotenv()
spotipy_client = SpotipyClient(spotipy_client=get_spotify_proxy())
telegram_client = TelegramClient(chat_id=None, token=os.environ['TELEGRAM_BOT_TOKEN'])


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.environ.get("VERCEL"):
        domain = os.environ['VERCEL_PROJECT_PRODUCTION_URL']
        response = requests.post(
            f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/setWebhook",
            json={"url": f"https://{domain}/api/webhook"},
        )

        if response.status_code == 200:
            logger.success(f"Webhook was set to '{domain}'")
        else:
            logger.error(
                f"Failed to set webhook '{domain}'. Response: {response.status_code} {response.json()}"
            )
    else:
        logger.debug("Webhook was not set as env is not vercel")
    yield


app = FastAPI(lifespan=lifespan)


def add_release_to_playlist(release_id: str, spotipy_client: SpotipyClient):
    songs_to_add_ids = []

    if "episode" in release_id:
        songs_to_add_ids.append(release_id)
    else:
        songs_ids = spotipy_client.get.get_album_songs(release_id)
        songs_to_add_ids.extend(songs_ids)

        songs_to_add_ids = [
            song for song in songs_to_add_ids
            if spotipy_client.get.favorite_artist_song(song)
        ]

    if not songs_to_add_ids:
        logger.info("No songs or episodes to add to playlist")
        return

    spotipy_client.post.add_songs_to_playlist(
        playlist_id=SPOTIFICATIONS_PLAYLIST_ID,
        songs_ids=songs_to_add_ids,
    )
    logger.info(f"Added to playlist: {songs_to_add_ids}")


@app.get("/")
def welcome():
    return HTMLResponse(content="<h1>Welcome to Spotification Webhook</h1>", status_code=200)


def handle_add_new_release(release_uri):
    add_release_to_playlist(release_uri, spotipy_client)
    release = spotipy_client.get.get_release(release_uri=release_uri)

    text = f"🎧 Added to playlist!\n\n🎶<b>{release.name}</b>"
    if release.artists:
        text = f"{text} by <b>{release.artists}</b>"

    telegram_client.send_message_with_image(
        image_url=release.cover_url,
        text=text,
        keyboard=telegram_client.compose_keyboard(
            NotificationKeyboardButton(
                url=SPOTIFICATIONS_PLAYLIST_LINK,
                text="Check ListenToMe playlist!",
            ).model_dump()
        )
    )


def handle_delete_track_from_playlist(track_uri: str):
    spotipy_client.post.delete_track(
        playlist_id=MAIN_PLAYLIST_ID,
        track_id=track_uri,
    )
    spotify_track_id = track_uri.rsplit(':', 1)[-1]
    track_url = f'https://open.spotify.com/track/{spotify_track_id}'
    telegram_client.send_message(
        f'Removed duplicate from playlist: <a href="{track_url}">open on Spotify</a>',
    )


@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    webhook_response = await request.json()
    query = webhook_response.get('callback_query')
    if not query:
        logger.debug("Webhook update without callback_query")
        return {"ok": True}

    data = json.loads(query['data'])
    telegram_client.chat_id = query['message']['chat']['id']

    delete_track_uri = data.get('delete_track_uri')
    if delete_track_uri is not None:
        handle_delete_track_from_playlist(track_uri=delete_track_uri)
        return {"ok": True}

    release_uri = data.get("release_uri")
    if release_uri is not None:
        handle_add_new_release(release_uri=release_uri)
        return {"ok": True}

    return {"ok": True}
