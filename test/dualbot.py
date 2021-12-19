import asyncio
import logging
import os

import pytest
from discord import Client
from discord.ext import commands

from main import DamaBot

# Discord bot tests with two simultaneous instances

guild = 822951335191904267
channel = 834125219052126228

_log = logging.getLogger(__name__)


async def wait_for_ready(*bots):
    while not all([b.is_ready() for b in bots]):
        await asyncio.sleep(.01)


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.new_event_loop()


@pytest.fixture(scope="session")
def testbot(event_loop):
    testbot = Client(loop=event_loop)
    event_loop.create_task(testbot.start(os.environ["TEST_TOKEN"]))
    event_loop.run_until_complete(wait_for_ready(testbot))
    return testbot


@pytest.fixture(scope="session")
def damabot(event_loop, testbot):
    async def process_commands(self, message) -> None:
        # Only respond to the testbot user
        if message.author.id != testbot.user.id:
            return
        ctx = await self.get_context(message)
        await self.invoke(ctx)

    commands.bot.BotBase.process_commands = process_commands

    damabot = DamaBot(loop=event_loop)
    event_loop.create_task(damabot.start(os.environ["DISCORD_TOKEN"]))
    event_loop.run_until_complete(wait_for_ready(damabot))
    return damabot


@pytest.mark.asyncio
async def test_ready(testbot, damabot):
    assert testbot.is_ready()
    assert damabot.is_ready()


@pytest.mark.asyncio
async def test_messaging(testbot, damabot):
    await testbot.get_channel(channel).send(".last register jsoifdjasoifj")
    result = await testbot.wait_for("message", check=lambda m: m.author.id == damabot.user.id, timeout=5)
    _log.info(result.content)
    assert result.content == "User does not exist."
