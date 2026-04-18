import datetime
import json

from clients.telegram_client import TelegramClient
from constants import (
    EPISODE_PATTERN,
    NOTITICATION_PATTERN,
    NO_NEW_RELEASES_IMAGE,
    SPOTIFICATIONS_PLAYLIST_LINK,
)
from models import NotificationKeyboardButton, Release


def notify_no_releases(telegram_client: TelegramClient, crawling_date: datetime.datetime):
    telegram_client.send_message_with_image(
        text=f'No new releases from {crawling_date.strftime("%d.%m.%Y")}',
        image_url=NO_NEW_RELEASES_IMAGE,
        keyboard=telegram_client.compose_keyboard(
            NotificationKeyboardButton(
                url=SPOTIFICATIONS_PLAYLIST_LINK,
                text="Check ListenToMe playlist!",
            ).model_dump()
        )
    )


def send_release_notification(telegram_client: TelegramClient, release: Release):
    text = NOTITICATION_PATTERN.format(
        artists=release.artists,
        release_date=release.release_date,
        release_name=release.name,
        release_link=release.url
    ) if release.artists else (
        EPISODE_PATTERN.format(
            release_date=release.release_date,
            release_name=release.name,
            release_link=release.url
        )
    )

    telegram_client.send_message_with_image(
        text=text,
        image_url=release.cover_url,
        keyboard=telegram_client.compose_keyboard(
            NotificationKeyboardButton(
                url=release.url,
                text=release.name,
            ).model_dump(exclude_none=True),
            NotificationKeyboardButton(
                text="❤️",
                callback_data=json.dumps({"release_uri": release.uri}),
            ).model_dump(exclude_none=True)
        )
    )
