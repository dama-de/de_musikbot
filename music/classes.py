from typing import Optional

import discord
import pylast


class NamedBase:
    __slots__ = ("name",)

    def __bool__(self):
        return bool(self.name)

    def __str__(self):
        return self.name


class Artist(NamedBase):
    __slots__ = ("url", "img_url", "tags", "popularity", "spotify_id")


class Track(NamedBase):
    __slots__ = ("_artist", "_album", "length", "url", "popularity", "spotify_id")

    def __init__(self):
        self._artist = Artist()
        self._album = Album()

    @property
    def artist(self):
        return self._artist

    @property
    def album(self):
        return self._album


class Album(NamedBase):
    __slots__ = ("_artist", "date", "tracks", "url", "img_url", "popularity", "spotify_id")

    def __init__(self):
        self._artist = Artist()

    @property
    def artist(self):
        return self._artist
