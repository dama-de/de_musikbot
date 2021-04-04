from music import lastfm_net, spotify_api
from music.classes import *


def search_lastfm_track(artist: str, title: str) -> Optional[Track]:
    result = lastfm_net.get_track(artist, title)

    if not result:
        return None

    return pack_lastfm_track(result)


def pack_lastfm_track(data: pylast.Track) -> Track:
    track = Track()
    track.name = data.get_name(properly_capitalized=True)
    track.artist.name = data.get_artist().get_name(properly_capitalized=True)
    track.url = data.get_url()

    if data.get_album():
        track.album.name = data.get_album().get_name()
        track.album.artist.name = data.get_album().artist.name
        track.album.img_url = data.get_album().get_cover_image(pylast.SIZE_MEGA)

    return track
