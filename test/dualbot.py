import asyncio
import os

import pytest
from discord import Client

from main import DamaBot


# Discord bot tests with two simultaneous instances

async def wait_for_ready(*bots):
    while not all([b.is_ready() for b in bots]):
        await asyncio.sleep(.01)


@pytest.fixture
def testbot(event_loop):
    testbot = Client(loop=event_loop)
    event_loop.create_task(testbot.start(os.environ["TEST_TOKEN"]))
    event_loop.run_until_complete(wait_for_ready(testbot))
    return testbot


@pytest.fixture
def damabot(event_loop):
    damabot = DamaBot(loop=event_loop)
    event_loop.create_task(damabot.start(os.environ["DISCORD_TOKEN"]))
    event_loop.run_until_complete(wait_for_ready(damabot))
    return damabot


@pytest.mark.asyncio
async def test_ready(testbot, damabot):
    assert testbot.is_ready()
    assert damabot.is_ready()
