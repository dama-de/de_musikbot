import asyncio
import logging
import os

import pytest
from discord import Client, Intents
from discord.ext import commands

from main import DamaBot

# Discord bot tests with two simultaneous instances

guild = 822951335191904267
channel = 938139112752422973

_log = logging.getLogger(__name__)


async def wait_for_ready(*bots):
    while not all([b.is_ready() for b in bots]):
        await asyncio.sleep(.01)


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.new_event_loop()


@pytest.fixture(scope="session")
def client(event_loop):
    client = Client(intents=Intents.all())
    event_loop.create_task(client.start(os.environ["TEST_TOKEN"]))
    event_loop.run_until_complete(wait_for_ready(client))
    return client


@pytest.fixture(scope="session")
def bot(event_loop, client):
    async def process_commands(self, message) -> None:
        # Only respond to the client user
        if message.author.id != client.user.id:
            return
        ctx = await self.get_context(message)
        await self.invoke(ctx)

    commands.bot.BotBase.process_commands = process_commands

    bot = DamaBot()
    event_loop.create_task(bot.start(os.environ["DISCORD_TOKEN"]))
    event_loop.run_until_complete(wait_for_ready(bot))
    return bot


@pytest.mark.asyncio
async def test_ready(client, bot):
    assert client.is_ready()
    assert bot.is_ready()

    assert "cogs.music" in bot.extensions
    assert "cogs.new" in bot.extensions


@pytest.mark.asyncio
async def test_messaging(client, bot):
    receiver = client.loop.create_task(
        client.wait_for("message", check=lambda m: m.author.id == bot.user.id, timeout=5)
    )

    await client.get_channel(channel).send(".last register jsoifdjasoifj")
    result = await receiver
    _log.info(result.content)
    assert result.content == "User does not exist."
