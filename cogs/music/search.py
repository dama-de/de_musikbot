import asyncio
import functools
import logging
import os
from typing import Optional, Union, List

import discord
import lyricsgenius
import pylast
import tekore
from tekore.model import SimpleAlbum, FullAlbum, SimpleArtist, FullArtist, FullTrack

from .classes import *

# This module provides lookup functions for various music services
# Notes:
# - Before importing the module, the following environment vars need to be set:
#       LAST_API_KEY, LAST_API_SECRET, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, GENIUS_CLIENT_SECRET
# - pylast is not async, so calls should be wrapped in asyncio.to_thread

_log = logging.getLogger(__name__)

# Init APIs
# TODO This should be moved to some place where it's not being run on import
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


def _get_lastfm_user(username: str) -> pylast.User:
    if not isinstance(username, str):
        raise TypeError("Username must be a str, but is " + username.__class__.__name__)
    return lastfm_net.get_user(username)


async def user_exists(username: str) -> bool:
    userobj = _get_lastfm_user(username)
    try:
        await asyncio.to_thread(userobj.get_registered)
        return True
    except pylast.WSError as err:
        if err.details == "User not found":
            return False
        raise err


async def get_recent(username: str) -> List[Track]:
    user = _get_lastfm_user(username)
    return await asyncio.to_thread(user.get_recent_tracks)


async def get_scrobble(username: str) -> Optional[Scrobble]:
    result = await asyncio.to_thread(lastfm_net.get_user(username).get_now_playing)
    return await asyncio.to_thread(_pack_lastfm_track, result)


async def search_lastfm_album(search: str) -> Optional[Album]:
    result = await asyncio.to_thread(lastfm_net.search_for_album(search).get_next_page)
    return await asyncio.to_thread(_pack_lastfm_album, result[0])


async def search_lastfm_track(artist: str, title: str) -> Optional[Track]:
    result = lastfm_net.get_track(artist, title)
    return await asyncio.to_thread(_pack_lastfm_track, result)


async def search_lastfm_artist(artist: str, exact=False) -> Optional[Artist]:
    if exact:
        result = lastfm_net.get_artist(artist)
    else:
        result = await asyncio.to_thread(lastfm_net.search_for_artist(artist).get_next_page)
        result = result[0] if result else None

    return await asyncio.to_thread(_pack_lastfm_artist, result)


def _pack_lastfm_artist(data: pylast.Artist) -> Optional[Artist]:
    if not isinstance(data, pylast.Artist):
        return None

    result = Artist()
    result.name = data.get_name(properly_capitalized=True)
    result.bio = data.get_bio("summary").split("<a href")[0]
    result.url = data.get_url()
    result.tags = ", ".join([t.item.name for t in data.get_top_tags(limit=6) if int(t.weight) >= 10])

    return result


async def search_spotify_artist(query: str) -> Optional[Artist]:
    result = await _search_spotify(query, types=("artist",))  # type: FullArtist
    return _pack_spotify_artist(result)


async def search_spotify_album(query: str, extended=False) -> Optional[Album]:
    result = await _search_spotify(query, types=("album",))  # type: SimpleAlbum

    if extended and result:
        result = await spotify_api.album(result.id)  # type: FullAlbum

    return _pack_spotify_album(result)


async def _build_spotify_query(query="", track=None, artist=None, album=None, year=None,
                               genre=None, upc=None, tag=None, isrc=None) -> str:
    """https://developer.spotify.com/documentation/web-api/reference/#/operations/search"""
    rquery = query
    rquery += f" track:{track}" if track else ""
    rquery += f" artist:{artist}" if artist else ""
    rquery += f" album:{album}" if album else ""
    rquery += f" genre:{genre}" if genre else ""
    rquery += f" year:{year}" if year else ""
    rquery += f" upc:{upc}" if upc else ""
    rquery += f" tag:{tag}" if tag else ""
    rquery += f" isrc:{isrc}" if isrc else ""
    return rquery.strip()


@functools.wraps(tekore.Spotify.search)
async def _search_spotify(*args, **kwargs) -> Union[FullTrack, SimpleAlbum, FullArtist, None]:
    """Search Spotify and return the best result"""

    # Force single result, we can't use more
    kwargs["limit"] = 1

    _log.debug(f"Querying Spotify: {args}, {kwargs}")
    result = await spotify_api.search(*args, **kwargs)

    # Try to extract the data object from the raw API response
    if result and result[0].items:
        return result[0].items[0]
    else:
        return None


async def search_spotify_track(query: str) -> Optional[Track]:
    result = await _search_spotify(query, types=("track",))
    return _pack_spotify_track(result)


def _pack_spotify_track(data: FullTrack) -> Optional[Track]:
    if not isinstance(data, FullTrack):
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


def _pack_spotify_artist(data: Union[SimpleArtist, FullArtist]) -> Optional[Artist]:
    if not isinstance(data, (SimpleArtist, FullArtist)):
        return None

    result = Artist()
    result.name = data.name
    result.tags = ", ".join(data.genres)
    result.popularity = data.popularity
    result.url = data.external_urls["spotify"]

    if data.images:
        result.img_url = data.images[0].url

    return result


def _pack_spotify_album(data: Union[SimpleAlbum, FullAlbum]) -> Optional[Album]:
    if not isinstance(data, (SimpleAlbum, FullAlbum)):
        return None

    result = Album()
    result.name = data.name
    result.artist.name = _join_spotify_artists(data)
    result.url = data.external_urls["spotify"]
    result.img_url = data.images[0].url
    result.date = data.release_date

    # Extended search returns a FullAlbum, which has some additional fields
    if isinstance(data, FullAlbum):
        result.length = sum([t.duration_ms for t in data.tracks.items])
        result.tracks = len(data.tracks.items)
        result.popularity = data.popularity

    return result


def _join_spotify_artists(data):
    return ", ".join([a.name for a in data.artists])


def _pack_lastfm_track(data: pylast.Track) -> Optional[Track]:
    if not data:
        return None

    track = Track()
    track.name = data.get_name()
    track.artist.name = data.get_artist().get_name()
    track.url = data.get_url()

    if data.get_album():
        track._album = _pack_lastfm_album(data.get_album())

    return track


def _pack_lastfm_scrobble(data: pylast.Track) -> Optional[Scrobble]:
    if not data:
        return None

    track = _pack_lastfm_track(data)


def _pack_lastfm_album(data: pylast.Album) -> Optional[Album]:
    if not data:
        return None

    album = Album()
    album.name = data.get_name()
    album.artist.name = data.get_artist().get_name()
    album.url = data.get_url()
    album.img_url = data.get_cover_image()

    return album


def _pack_spotify_activity(activity: discord.Spotify) -> Optional[Track]:
    if not activity:
        return None

    result = Track()
    result.name = activity.title
    result.length = int(activity.duration.total_seconds())
    result.url = "https://open.spotify.com/track/" + activity.track_id
    result.artist.name = ", ".join(activity.artists)
    result.album.name = activity.album
    result.album.img_url = activity.album_cover_url
    return result
