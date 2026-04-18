import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from clients.spotipy_client import SpotipyClient, get_spotipy_client
from loguru import logger


def _get_show_episodes_worker(show_id: str, newer_than: datetime.datetime):
    worker_client = get_spotipy_client()
    return set(worker_client.get.get_show_episodes(show_id=show_id, newer_than=newer_than))


def get_shows_latest_episodes(client: SpotipyClient, newer_than: datetime.datetime, number_of_workers: int):
    logger.debug("Retrieving shows ids")
    shows_ids = client.get.get_favorite_shows()

    logger.debug(f"Crawling episodes newer than {newer_than}")

    new_episodes = set()
    with ThreadPoolExecutor(max_workers=number_of_workers) as executor:
        futures = [
            executor.submit(
                _get_show_episodes_worker,
                show_id=show_id,
                newer_than=newer_than,
            )
            for show_id in shows_ids
        ]

        for index, future in enumerate(as_completed(futures), start=1):
            episodes = future.result()
            if episodes:
                new_episodes.update(episodes)
            logger.info(f"Processed {index}/{len(shows_ids)} shows")

    return new_episodes
