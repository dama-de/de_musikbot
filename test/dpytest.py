import os
import tempfile

import discord
import discord.ext.test as dpytest
import pytest
from discord.ext.commands import CommandInvokeError

# Discord bot tests using dpytest
# Notes:
# - Testing commands only works correctly if the bot has the members intent enabled

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

# Do not load SlashCommand, as it breaks dpytest
os.environ["SKIP_SLASH"] = "1"


@pytest.fixture
async def damabot(event_loop, tmp_path):
    with tempfile.TemporaryDirectory() as tempdir:
        os.environ["DATA_DIR"] = tempdir

        from main import DamaBot
        bot = DamaBot()
        dpytest.configure(bot)

        yield bot

        # Clean up any unretrieved messages to avoid spillover into next test
        await dpytest.empty_queue()


async def test_register(damabot):
    # Send register message and check for correct reaction response from bot
    msg = await dpytest.message(".last register bla")
    assert msg.reactions
    assert msg.reactions[0].emoji == "\N{WHITE HEAVY CHECK MARK}"

    # Confirm that the config has been updated correctly
    from util.config import Config
    config = Config("music")
    assert str(msg.author.id) in config.data["names"]
    assert config.data["names"][str(msg.author.id)] == "bla"


async def test_unregistered(damabot):
    with pytest.raises(CommandInvokeError) as err:
        await dpytest.message(".last recent")
    assert err.value.original.__class__.__name__ == "NotRegisteredError"


async def test_recent(damabot):
    await dpytest.message(".last register dam4rusxp")
    await dpytest.message(".last recent")

    embed = discord.Embed()
    embed.title = "Recent scrobbles"
    assert dpytest.verify().message().embed(embed)


async def test_wrong_period(damabot):
    await dpytest.message(".last tracks lh")
    assert dpytest.verify().message().contains().content("Unknown time-period.")


async def test_spotify_error(damabot):
    pass


async def test_lastfm_error(damabot):
    pass
