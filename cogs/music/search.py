import asyncio
import os
from typing import Optional

import discord
import lyricsgenius
import pylast
import tekore
from tekore._model import SimpleAlbum, FullAlbum, SimpleArtist, FullArtist, FullTrack

from .classes import *

lastfm_net = pylast.LastFMNetwork(
    api_key=(os.environ["LAST_API_KEY"]),
    api_secret=(os.environ["LAST_API_SECRET"]))

spotify_api = tekore.Spotify(
    tekore.request_client_token(
        os.environ["SPOTIFY_CLIENT_ID"],
        os.environ["SPOTIFY_CLIENT_SECRET"]),
    asynchronous=True)

genius = lyricsgenius.Genius(
    os.environ["GENIUS_CLIENT_SECRET"])


async def get_scrobble(username: str) -> Optional[Track]:
    result = await asyncio.to_thread(lastfm_net.get_user(username).get_now_playing)
    return await asyncio.to_thread(pack_lastfm_track, result)


async def search_lastfm_album(search: str) -> Optional[Album]:
    result = await asyncio.to_thread(lastfm_net.search_for_album(search).get_next_page)
    return await asyncio.to_thread(pack_lastfm_album, result[0])


async def search_lastfm_track(artist: str, title: str) -> Optional[Track]:
    result = lastfm_net.get_track(artist, title)
    return await asyncio.to_thread(pack_lastfm_track, result)


async def search_lastfm_artist(artist: str, exact=False) -> Optional[Artist]:
    if exact:
        result = lastfm_net.get_artist(artist)
    else:
        result = await asyncio.to_thread(lastfm_net.search_for_artist(artist).get_next_page)
        result = result[0]

    return await asyncio.to_thread(pack_lastfm_artist, result)


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
    result.album.name = data.album.name
    result.album.artist.name = _join_spotify_artists(data.album)
    result.album.img_url = data.album.images[0].url
    result.album.date = data.album.release_date
    result.artist.name = _join_spotify_artists(data)

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
    result.artist.name = _join_spotify_artists(data)
    result.url = data.external_urls["spotify"]
    result.img_url = data.images[0].url
    result.date = data.release_date

    if isinstance(data, FullAlbum):
        result.length = sum([t.duration_ms for t in data.tracks.items])
        result.tracks = len(data.tracks.items)

    return result


def _join_spotify_artists(data):
    return ", ".join([a.name for a in data.artists])


def pack_lastfm_track(data: pylast.Track) -> Optional[Track]:
    if not data:
        return None

    track = Track()
    track.name = data.get_name()
    track.artist.name = data.get_artist().get_name()
    track.url = data.get_url()

    if data.get_album():
        track._album = pack_lastfm_album(data.get_album())

    return track


def pack_lastfm_album(data: pylast.Album) -> Optional[Album]:
    if not data:
        return None

    album = Album()
    album.name = data.get_name()
    album.artist.name = data.get_artist().get_name()
    album.url = data.get_url()
    album.img_url = data.get_cover_image()

    return album


def pack_spotify_activity(activity: discord.Spotify) -> Optional[Track]:
    if not activity:
        return None

    result = Track()
    result.name = activity.title
    result.length = int(activity.duration.total_seconds())
    result.url = "https://open.spotify.com/track/" + activity.track_id
    result.artist.name = activity.artist
    result.album.name = activity.album
    result.album.img_url = activity.album_cover_url
    return result
