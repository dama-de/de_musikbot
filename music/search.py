from tekore._model import SimpleAlbum, FullAlbum, SimpleArtist, FullArtist, SimpleTrack, FullTrack

from music import lastfm_net, spotify_api
from music.classes import *


def get_scrobble(username: str) -> Optional[Track]:
    result = lastfm_net.get_user(username).get_now_playing()
    return pack_lastfm_track(result)


def search_lastfm_track(artist: str, title: str) -> Optional[Track]:
    result = lastfm_net.get_track(artist, title)
    return pack_lastfm_track(result)


def search_lastfm_artist(artist: str, exact=False) -> Optional[Artist]:
    if exact:
        result = lastfm_net.get_artist(artist)
    else:
        result = lastfm_net.search_for_artist(artist).get_next_page()[0]

    return pack_lastfm_artist(result)


def pack_lastfm_artist(data: pylast.Artist) -> Optional[Artist]:
    if not isinstance(data, pylast.Artist):
        return None

    result = Artist()
    result.name = data.get_name(properly_capitalized=True)
    result.bio = data.get_bio("summary").split("<a href")[0]
    result.url = data.get_url()
    result.tags = ", ".join([t.item.name for t in data.get_top_tags(limit=6) if int(t.weight) >= 10])

    return result


async def search_spotify_artist(query: str, extended=False) -> Optional[Artist]:
    result = await spotify_api.search(query, types=("artist",), limit=1)

    if result and result[0].items:
        sp_artist = result[0].items[0]  # type: SimpleArtist
    else:
        return None

    if extended:
        sp_artist = await spotify_api.artist(sp_artist.id)  # type: FullArtist

    return pack_spotify_artist(sp_artist)


async def search_spotify_album(query: str, extended=False) -> Optional[Album]:
    result = await spotify_api.search(query, types=("album",), limit=1)

    if result and result[0].items:
        sp_album = result[0].items[0]  # type: SimpleAlbum
    else:
        return None

    if extended:
        sp_album = await spotify_api.album(sp_album.id)  # type: FullAlbum

    return pack_spotify_album(sp_album)


async def search_spotify_track(query: str) -> Optional[Track]:
    result = await spotify_api.search(query, types=("track",), limit=1)

    if result and result[0].items:
        sp_track = result[0].items[0]  # type: FullTrack
    else:
        return None

    return pack_spotify_track(sp_track)


def pack_spotify_track(data) -> Optional[Track]:
    if not isinstance(data, (FullTrack,)):
        return None

    result = Track()
    result.name = data.name
    result.url = data.external_urls["spotify"]
    result.album.img_url = data.album.images[0].url
    result.album.date = data.album.release_date

    return result


def pack_spotify_artist(data) -> Optional[Artist]:
    if not isinstance(data, (SimpleArtist, FullArtist)):
        return None

    result = Artist()
    result.name = data.name
    result.tags = ", ".join(data.genres)
    result.popularity = data.popularity
    result.url = data.external_urls["spotify"]
    result.img_url = data.images[0].url

    return result


def pack_spotify_album(data) -> Optional[Album]:
    if not isinstance(data, (SimpleAlbum, FullAlbum)):
        return None

    result = Album()
    result.name = data.name
    result.artist.name = ", ".join([a.name for a in data.artists])
    result.url = data.external_urls["spotify"]
    result.img_url = data.images[0].url
    result.date = data.release_date

    if isinstance(data, FullAlbum):
        result.length = sum([t.duration_ms for t in data.tracks.items])
        result.tracks = len(data.tracks.items)

    return result


def pack_lastfm_track(data: pylast.Track) -> Optional[Track]:
    if not data:
        return None

    track = Track()
    track.name = data.get_name(properly_capitalized=True)
    track.artist.name = data.get_artist().get_name(properly_capitalized=True)
    track.url = data.get_url()

    if data.get_album():
        track.album.name = data.get_album().get_name()
        track.album.artist.name = data.get_album().artist.name
        track.album.img_url = data.get_album().get_cover_image(pylast.SIZE_MEGA)

    return track
