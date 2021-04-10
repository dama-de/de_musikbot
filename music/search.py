from tekore._model import SimpleAlbum, FullAlbum

from music import lastfm_net, spotify_api
from music.classes import *


def get_scrobble(username: str) -> Optional[Track]:
    result = lastfm_net.get_user(username).get_now_playing()
    return pack_lastfm_track(result)


def search_lastfm_track(artist: str, title: str) -> Optional[Track]:
    result = lastfm_net.get_track(artist, title)
    return pack_lastfm_track(result)


async def search_spotify_album(query: str, extended=False) -> Optional[Album]:
    result = await spotify_api.search(query, types=("album",), limit=1)

    if result and result[0].items:
        sp_album = result[0].items[0]  # type: SimpleAlbum
    else:
        return None

    if extended:
        sp_album = await spotify_api.album(sp_album.id)  # type: FullAlbum

    return pack_spotify_album(sp_album)


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
