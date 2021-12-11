import asyncio
import os
from unittest.mock import AsyncMock

import dotenv
import pytest
from pytest_mock import MockFixture


# pytest directory-wide configuration file
# https://docs.pytest.org/en/6.2.x/writing_plugins.html#conftest-py-local-per-directory-plugins


@pytest.fixture(scope="session")
def event_loop():
    """We need to supply our own broadly scoped event_loop for the async search fixture to work"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def search():
    """Closes the Spotify API after the tests, to avoid an error in the log"""
    from cogs.music import search
    yield search
    await search.spotify_api.close()


@pytest.fixture(scope="session", autouse=True)
def setup_env():
    """Load the .env for the whole test suite"""
    env_file = dotenv.find_dotenv(".env")
    dotenv.load_dotenv(env_file)


@pytest.fixture(scope="function")
def setup_mock_env(mocker: MockFixture):
    mocker.patch.dict(os.environ, {
        "LAST_API_KEY": "",
        "LAST_API_SECRET": "",
        "SPOTIFY_CLIENT_ID": "",
        "SPOTIFY_CLIENT_SECRET": "",
        "GENIUS_CLIENT_SECRET": ""}
                      )


@pytest.fixture(scope="function")
def mock_search_apis(mocker: MockFixture):
    mocker.patch("pylast.LastFMNetwork")
    mocker.patch("tekore.Spotify", return_value=AsyncMock())
    mocker.patch("tekore.request_client_token")
    mocker.patch("lyricsgenius.Genius")
