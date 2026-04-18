import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from clients.spotipy_client import SpotipyClient, get_spotipy_client
from loguru import logger


def _get_artist_releases_worker(artist_id: str, newer_than: datetime.datetime):
    worker_client = get_spotipy_client()
    return set(worker_client.get.get_artist_releases(artist_id=artist_id, newer_than=newer_than))


def get_artists_latest_releases(client: SpotipyClient, newer_than: datetime.datetime, number_of_workers: int):
    logger.debug("Retrieving artists ids")
    artists_ids = client.get.get_artists_ids()

    logger.debug(f"Crawling releases newer than {newer_than}")

    new_releases = set()
    with ThreadPoolExecutor(max_workers=number_of_workers) as executor:
        futures = [
            executor.submit(
                _get_artist_releases_worker,
                artist_id=artist_id,
                newer_than=newer_than,
            )
            for artist_id in artists_ids
        ]

        for index, future in enumerate(as_completed(futures), start=1):
            releases = future.result()
            if releases:
                new_releases.update(releases)
            logger.info(f"Processed {index}/{len(artists_ids)} artists")

    return new_releases
