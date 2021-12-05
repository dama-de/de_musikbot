import asyncio

import pytest

# Tests for the cogs.music.search module

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

@pytest.fixture(scope="module")
def event_loop():
    """We need to supply our own broadly scoped event_loop for the async search fixture to work"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def search():
    """Closes the Spotify API after the tests, to avoid an error in the log"""
    from cogs.music import search
    yield search
    await search.spotify_api.close()


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
