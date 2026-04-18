import datetime
import os
import json
from dotenv import load_dotenv

from artists_crawler import get_artists_latest_releases
from shows_crawler import get_shows_latest_episodes
from clients.spotipy_client import get_spotipy_client
from clients.telegram_client import TelegramClient
from constants import TELEGRAM_CHAT_ID
from notifications import notify_no_releases, send_release_notification
from loguru import logger

load_dotenv()


def get_processed_releases_uris():
    with open(".processed_releases_uris") as file:
        return json.load(fp=file)["uris"]


def save_processed_releases_uris(uris):
    with open(".processed_releases_uris", "w") as file:
        return json.dump({"uris": uris}, fp=file)


def update_last_crawling_date(last_crawling_date):
    with open(".last_crawling_date", "w") as file:
        file.write(str(last_crawling_date))


def get_last_crawling_date():
    with open(".last_crawling_date") as file:
        return datetime.datetime.fromisoformat(file.readline())


def main():
    shared_spotipy_client = get_spotipy_client()
    number_of_workers = int(os.environ.get("SPOTIFY_RELEASES_WORKERS", "4"))
    telegram_client = TelegramClient(
        chat_id=TELEGRAM_CHAT_ID,
        token=os.environ['TELEGRAM_BOT_TOKEN'],
    )

    last_crawling_date = get_last_crawling_date()
    processed_releases_uris = get_processed_releases_uris()

    new_releases = get_artists_latest_releases(
        client=shared_spotipy_client,
        newer_than=last_crawling_date,
        number_of_workers=number_of_workers,
    )

    new_episodes = get_shows_latest_episodes(
        client=shared_spotipy_client,
        newer_than=last_crawling_date,
        number_of_workers=number_of_workers,
    )
    releases_to_notify = [
        *[
            release for release in new_releases
            if release.uri not in processed_releases_uris
        ],
        *[
            episode for episode in new_episodes
            if episode.uri not in processed_releases_uris
        ]
    ]

    if not releases_to_notify:
        notify_no_releases(telegram_client=telegram_client, crawling_date=last_crawling_date)
    else:
        for release in releases_to_notify:
            send_release_notification(telegram_client=telegram_client, release=release)

    now = datetime.datetime.now().date()
    update_last_crawling_date(now)

    save_processed_releases_uris([release.uri for release in releases_to_notify])

    logger.success(f"Crawling finished. Last crawling date set to: {now}")


if __name__ == "__main__":
    main()
