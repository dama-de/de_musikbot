import pytest

# Tests for the cogs.music.search module

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio


async def test_get_scrobble(search, mocker):
    # Mock pylast to always supply a scrobble
    track = search.lastfm_net.get_track_by_mbid("50347f42-2a40-4df6-b358-07f994af7a3f")
    get_scrobble_patch = mocker.patch("pylast.User.get_now_playing")
    get_scrobble_patch.return_value = track

    result = await search.get_scrobble("dam4rusxp")
    assert result.name == "What I've Done"
    assert result.artist.name == "Linkin Park"


async def test_search_spotify_track(search):
    result = await search.search_spotify_track("track:What I've Done artist:Linkin Park")
    assert result.name == "What I've Done"
    assert result.artist.name == "Linkin Park"


async def test_search_spotify_album(search):
    result = await search.search_spotify_album("album:Minutes to Midnight artist:Linkin Park", extended=False)
    assert result.name == "Minutes to Midnight"
    assert result.artist.name == "Linkin Park"


async def test_search_spotify_artist(search):
    result = await search.search_spotify_artist("Linkin Park")
    assert result.name == "Linkin Park"


async def test_search_lastfm_track(search):
    result = await search.search_lastfm_track("Linkin Park", "What I've Done")
    assert result.name == "What I've Done"
    assert result.artist.name == "Linkin Park"


async def test_search_lastfm_album(search):
    result = await search.search_lastfm_album("Linkin Park Minutes to Midnight")
    assert result.name == "Minutes to Midnight"
    assert result.artist.name == "Linkin Park"
    assert result.artist.name == "Linkin Park"


async def test_search_spotify_album(search):
    result = await search.search_spotify_album("album:Minutes to Midnight artist:Linkin Park", extended=False)
    assert result.name == "Minutes to Midnight"
    assert result.artist.name == "Linkin Park"


async def test_search_spotify_artist(search):
    result = await search.search_spotify_artist("Linkin Park")
    assert result.name == "Linkin Park"


async def test_search_lastfm_track(search):
    result = await search.search_lastfm_track("Linkin Park", "What I've Done")
    assert result.name == "What I've Done"
    assert result.artist.name == "Linkin Park"


async def test_search_lastfm_album(search):
    result = await search.search_lastfm_album("Linkin Park Minutes to Midnight")
    assert result.name == "Minutes to Midnight"
    assert result.artist.name == "Linkin Park"
