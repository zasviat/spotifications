from dotenv import load_dotenv
from loguru import logger
import os

from clients.spotipy_client import get_spotipy_client
from clients.telegram_client import TelegramClient
from constants import MAIN_PLAYLIST_ID, TELEGRAM_CHAT_ID
from notifications import send_duplicate_group_notification


load_dotenv()


def get_duplicates():
    spotipy_client = get_spotipy_client()
    return spotipy_client.get.get_playlist_duplicates(playlist_id=MAIN_PLAYLIST_ID)


def send_duplicate_notifications(duplicates: dict) -> None:
    spotipy_client = get_spotipy_client()
    telegram_client = TelegramClient(
        chat_id=TELEGRAM_CHAT_ID,
        token=os.environ['TELEGRAM_BOT_TOKEN'],
    )

    for (_, _artist_ids), track_uris in duplicates.items():
        if len(track_uris) < 2:
            continue

        first_track = spotipy_client.get.get_track(track_uris[0])
        images = (first_track.get("album") or {}).get("images") or []
        cover_url = images[0]["url"] if images else None

        playlist_rows = []
        for uri in track_uris:
            row_track = spotipy_client.get.get_track(uri)
            row_name = row_track["name"]
            row_artists = ", ".join(a["name"] for a in row_track["artists"])
            row_album = (row_track.get("album") or {}).get("name") or ""
            playlist_rows.append((uri, row_name, row_artists, row_album))

        send_duplicate_group_notification(
            telegram_client,
            playlist_rows=playlist_rows,
            cover_url=cover_url,
        )


def main():
    duplicates = get_duplicates()
    logger.info(f"Found {len(duplicates)} groups")
    send_duplicate_notifications(duplicates)


if __name__ == "__main__":
    main()
