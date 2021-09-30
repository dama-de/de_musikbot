class NamedBase:
    name: str = None

    def __bool__(self):
        return bool(self.name)

    def __str__(self):
        return self.name

    def update(self, data):
        for key in data.__dict__:
            value = getattr(data, key)

            if not value:
                continue

            if isinstance(value, NamedBase):
                getattr(self, key).update(value)
            else:
                setattr(self, key, value)


class Artist(NamedBase):
    bio: str
    url: str
    img_url: str
    tags: str
    popularity: int


class Track(NamedBase):
    length: int
    url: str
    popularity: int

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
    date: str
    tracks: int
    length: int
    url: str
    img_url: str
    popularity: int

    def __init__(self):
        self._artist = Artist()

    @property
    def artist(self):
        return self._artist
