from datetime import datetime
from typing import Optional, List, Tuple
from pathlib import Path
import os
import sys
from loguru import logger
sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.models import Release  # noqa: E402

DEFAULT_RELEASES_GROUPS = ",".join(("album", "single", "compilation", "appears_on"))
VARIOUS_ARTISTS = "Various Artists"


class GetSpotipyClient:
    def __init__(self, spotipy_client):
        self.client = spotipy_client

    def get_playlist_duplicates(self, playlist_id: str):
        duplicates = {}
        offset = 0
        while True:
            songs, limit, total = self._get_playlist_songs(playlist_id, offset)

            for song in songs:
                duplicates.setdefault(song['track']["name"], []).append(song['track']["uri"])
            logger.debug(f"Get songs of playlist {playlist_id}. Offset: {offset}")
            if total <= offset:
                break
            offset += limit
        breakpoint()
        return {k: v for k, v in duplicates.items() if len(v) > 1}

    def get_track(self, track_id: str):
        return self.client.track(track_id)

    def _get_playlist_songs(self, playlist_id: str, offset: int = 0):
        """Get songs from specific playlist"""
        response = self.client.playlist_tracks(playlist_id, offset=offset)
        logger.debug(f"Get songs of playlist {playlist_id}. Offset: {offset}")

        return response["items"], response["limit"], response["total"]

    def get_artist_releases(self, artist_id: str, newer_than: Optional[datetime]):
        """Get specific artist's releases newer than provided date"""
        artist_releases = []
        offset = 0
        while True:
            releases, limit, total = self._get_artist_releases(artist_id, newer_than, offset)
            logger.debug(
                f"Get artist {artist_id} releases. Newer than: {newer_than}. Offset: {offset}"
            )
            artist_releases.extend(releases)

            if os.environ.get('SPOTIFICATIONS_DEBUG'):
                break

            if total <= offset:
                break

            offset += limit

        return artist_releases

    def get_show_episodes(self, show_id: str, newer_than: Optional[datetime]):
        """Get specific show's episodes newer than provided date"""
        show_episodes = []
        offset = 0
        while True:
            episodes, limit, total = self._get_show_episodes(show_id, newer_than, offset)
            logger.debug(
                f"Get episodes for {show_id} show. Newer than: {newer_than}. Offset: {offset}"
            )
            show_episodes.extend(episodes)

            if os.environ.get('SPOTIFICATIONS_DEBUG'):
                break

            if total <= offset:
                break

            offset += limit

        return show_episodes

    def get_artists_ids(self):
        """Get ids of artists that user follows """

        followed_artists_ids = []
        after = None
        while True:
            ids, has_next = self._get_artists_ids(after=after)
            logger.debug("Get artists ids")
            followed_artists_ids.extend(ids)

            if os.environ.get('SPOTIFICATIONS_DEBUG'):
                break

            if not has_next:
                break

            after = ids[-1]

        return followed_artists_ids

    def get_favorite_shows(self):
        """Get ids of shows that user saved"""
        saved_shows_ids = []
        offset = 0
        while True:
            ids, limit, total = self._get_favorite_shows(offset)
            logger.debug(f"Get favorite shows. Offset: {offset}")
            saved_shows_ids.extend(ids)

            if os.environ.get('SPOTIFICATIONS_DEBUG'):
                break

            if total <= offset:
                break

            offset += limit

        return saved_shows_ids

    def get_album_songs(self, album_id: str):
        """Get songs from specific album"""
        album_songs = self.client.album_tracks(album_id)['items']
        logger.debug(f"Get songs of album {album_id}")
        return [song['uri'] for song in album_songs]

    def favorite_artist_song(self, song_id: str) -> bool:
        song = self.client.track(song_id)
        artists_ids = [artist['id'] for artist in song['artists']]
        logger.debug(f"Check song {song_id} is from favorite artist")
        return any(self.client.current_user_following_artists(artists_ids))

    def _get_artists_ids(self, after=None) -> tuple:
        artists = self.client.current_user_followed_artists(after=after)['artists']
        return [item['id'] for item in artists['items']], artists['next']

    def _get_artist_releases(
            self, artist_id: str, newer_than: Optional[datetime], offset=None
    ) -> Tuple[List[Release], str, str]:
        if newer_than is None:
            newer_than = datetime.now()

        response = self.client.artist_albums(
            artist_id=artist_id, offset=offset, include_groups=DEFAULT_RELEASES_GROUPS,
        )

        return [
            Release.from_spotipy(release)
            for release in response["items"]
            if not self.skip_release(release, newer_than)
        ], response['limit'], response['total']

    def _get_favorite_shows(self, offset=None) -> tuple:
        shows = self.client.current_user_saved_shows(offset=offset)
        return [item['show']['id'] for item in shows['items']], shows['limit'], shows['total']

    def _get_show_episodes(
            self, show_id: str, newer_than: Optional[datetime], offset=None
    ) -> Tuple[List[Release], str, str]:
        if newer_than is None:
            newer_than = datetime.now()

        response = self.client.show_episodes(
            show_id=show_id, offset=offset,
        )

        return [
            Release.from_spotipy(episode)
            for episode in response["items"]
            if not self.skip_episode(episode, newer_than)
        ], response['limit'], response['total']

    @staticmethod
    def skip_release(release, newer_than) -> bool:
        release_date = Release.parse_release_date(release['release_date'])
        return any((
            VARIOUS_ARTISTS in {artists['name'] for artists in release['artists']},
            release is None or release_date < newer_than or release_date > datetime.now(),
        ))

    @staticmethod
    def skip_episode(episode, newer_than) -> bool:
        release_date = Release.parse_release_date(episode['release_date'])
        return any((
            episode is None or release_date < newer_than or release_date > datetime.now(),
        ))

    def get_release(self, release_uri: str):
        spotify_function = self.client.album
        if "episode" in release_uri:
            spotify_function = self.client.episode

        return Release.from_spotipy(spotify_function(release_uri))
