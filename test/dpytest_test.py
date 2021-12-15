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


@pytest.mark.parametrize(
    # @formatter:off
    "scrobble_artist, scrobble_title, embed_title, embed_description, embed_footer, embed_url, embed_thumbnail", [
        ("Low Roar", "Don't Be so Serious", "Low Roar - Don't Be So Serious", "Once In a Long, Long While... (2017)", "Now scrobbling on last.fm", "https://open.spotify.com/track/03RS5t6vNp1mw3zdGYCgwb", "https://i.scdn.co/image/ab67616d0000b2738c4171c2088bf9f3f08bd2dd"),
        ('Mito Tsukino', '浮遊感UFO', 'Mito Tsukino - 浮遊感UFO', '月の兎はヴァーチュアルの夢をみる (2021)', 'Now scrobbling on last.fm', 'https://open.spotify.com/track/1E5ET8QkpofNJZSNRmjzVT', 'https://i.scdn.co/image/ab67616d0000b273f4de85f41ea577077468f614'),
        ('Kropp', 'Din Kropp', 'Kropp - Din Kropp', 'Kropp (2014)', 'Now scrobbling on last.fm', 'https://open.spotify.com/track/5NRCABovvUwHjYRfzAx5tL', 'https://i.scdn.co/image/ab67616d0000b273d284b29956ed2f49dae05b24'),
    ])
    # @formatter:on
async def test_now(damabot, search, mocker, scrobble_artist, scrobble_title, embed_title, embed_description,
                   embed_footer, embed_url, embed_thumbnail):
    track = search.lastfm_net.search_for_track(scrobble_artist, scrobble_title).get_next_page()[0]
    get_scrobble_patch = mocker.patch("pylast.User.get_now_playing")
    get_scrobble_patch.return_value = track

    await dpytest.message(".last register anon")
    await dpytest.message(".last now")

    embed = dpytest.get_message().embeds[0]
    _log.info('Copy paste this for new parameters:\n'
              f'("{scrobble_artist}", "{scrobble_title}", "{embed.title}", "{embed.description}",'
              f' "{embed.footer.text}", "{embed.url}", "{embed.thumbnail.url}"),')
    assert embed.title == embed_title
    assert embed.description == embed_description
    assert embed.url == embed_url
    assert embed.thumbnail.url == embed_thumbnail
    assert embed.footer.text == embed_footer


async def test_last_my(damabot):
    await dpytest.message(".last register dam4rusxp")
    await dpytest.message(".last my")
    assert dpytest.verify().message().content("https://www.last.fm/user/dam4rusxp")
