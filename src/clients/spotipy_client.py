from .spotipy_clients import GetSpotipyClient, PostSpotipyClient
from loguru import logger
from proxy import get_spotify_proxy


class SpotipyClient:
    def __init__(self, spotipy_client):
        self.client = spotipy_client

        self.get = GetSpotipyClient(self.client)
        self.post = PostSpotipyClient(self.client)

        logger.success("Initialized new Spotipy client")


def get_spotipy_client():
    return SpotipyClient(spotipy_client=get_spotify_proxy())
