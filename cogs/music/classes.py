import datetime

import pylast


class NamedBase:
    name: str = ""

    def __bool__(self):
        return bool(self.name)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def update(self, data):
        if not data:
            return

        for key in data.__dict__:
            value = getattr(data, key)

            if not value:
                continue

            if isinstance(value, NamedBase):
                getattr(self, key).update(value)
            else:
                setattr(self, key, value)


class Artist(NamedBase):
    bio: str = None
    url: str = None
    img_url: str = None
    tags: str = None
    popularity: int = None
    origin: pylast.Artist = None


class Track(NamedBase):
    length: int = None
    url: str = None
    popularity: int = None
    origin: pylast.Track = None

    def __init__(self):
        self._artist = Artist()
        self._album = Album()

    @property
    def artist(self):
        return self._artist

    @property
    def album(self):
        return self._album


class Scrobble(Track):
    user: str = None
    live: bool = False
    time_start: datetime.datetime = None
    time_finish: datetime.datetime = None

    def __init__(self, track: Track):
        print(track)


class Album(NamedBase):
    date: str = None
    tracks: int = None
    length: int = None
    url: str = None
    img_url: str = None
    popularity: int = None
    origin: pylast.Album = None

    def __init__(self):
        self._artist = Artist()

    @property
    def artist(self):
        return self._artist
