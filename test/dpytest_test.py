import logging
import os
import tempfile

import discord
import discord.ext.test as dpytest
import pytest
from discord.ext.commands import CommandInvokeError

# Discord bot tests using dpytest
# Notes:
# - Testing commands only works correctly if the bot has the members intent enabled
# - The warning "Queues are not empty!" will be logged if some messages or errors were not checked

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

# Do not load SlashCommand, as it breaks dpytest
os.environ["SKIP_SLASH"] = "1"

_log = logging.getLogger(__name__)


@pytest.fixture
async def damabot(event_loop, tmp_path):
    with tempfile.TemporaryDirectory() as tempdir:
        os.environ["DATA_DIR"] = tempdir

        from main import DamaBot
        bot = DamaBot()
        dpytest.configure(bot)

        yield bot

        # Clean up any unretrieved messages to avoid spillover into next test
        if not dpytest.sent_queue.empty() or not dpytest.error_queue.empty():
            _log.warning("Queues are not empty!")
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


async def test_register_user_does_not_exist(damabot):
    await dpytest.message(".last register jsoifdjasoifj")
    assert dpytest.verify().message().content("User does not exist.")


async def test_unregistered(damabot):
    with pytest.raises(CommandInvokeError) as err:
        await dpytest.message(".last recent")
    assert err.value.original.__class__.__name__ == "NotRegisteredError"
    assert err.value.original.user == dpytest.get_config().members[0]
    assert dpytest.verify().message().content("You must register with `/last register` first.")


async def test_recent(damabot):
    await dpytest.message(".last register dam4rusxp")
    await dpytest.message(".last recent")

    embed = discord.Embed()
    embed.title = "Recent scrobbles"
    assert dpytest.verify().message().embed(embed)


async def test_wrong_period(damabot):
    await dpytest.message(".last tracks lh")
    assert dpytest.verify().message().contains().content("Unknown time-period.")


async def test_last_my(damabot):
    await dpytest.message(".last register dam4rusxp")
    await dpytest.message(".last my")
    assert dpytest.verify().message().content("https://www.last.fm/user/dam4rusxp")


async def test_artist_missing_spotify_image(damabot):
    await dpytest.message(".artist \"Mikkel Rev\"")
    msg = dpytest.get_message()
    assert msg.embeds
