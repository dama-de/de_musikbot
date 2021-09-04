import asyncio
import logging
from functools import wraps

from discord import NotFound
from discord_slash import SlashContext

_log = logging.getLogger(__name__)


def auto_defer(func):
    @wraps(func)
    async def decorator(*args, **kwargs):
        # Try to find the SlashContext in the parameters
        ctx = next(x for x in args if isinstance(x, SlashContext))
        if not ctx:
            raise Exception("Could not find SlashContext parameter")

        async def delayed_defer():
            await asyncio.sleep(1.5)
            if not ctx.responded:
                try:
                    await ctx.defer()
                except NotFound:
                    # If the interaction has already diappeared, there's nothing we can do
                    _log.warning("Defer happened after the interaction had disappeared")

        # Run delayed_defer in parallel with the command, so that it can automatically make the defer call,
        # if command execution takes too long.
        asyncio.create_task(delayed_defer())

        # Run the actual command
        await func(*args, **kwargs)

    return decorator
