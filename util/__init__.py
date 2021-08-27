import asyncio
import logging
from functools import wraps

from discord_slash import SlashContext


def auto_defer(func):
    @wraps(func)
    async def decorator(*args, **kwargs):
        ctx = next(x for x in args if isinstance(x, SlashContext))
        if not ctx:
            raise Exception("Could not find SlashContext parameter")

        async def delayed_defer():
            await asyncio.sleep(2)
            if not ctx.responded:
                await ctx.defer()

        asyncio.create_task(delayed_defer())

        try:
            await func(*args, **kwargs)
        except Exception as e:
            logging.error("An Exception occurred during deferred execution.", exc_info=e)
            await ctx.send("There was an error processing your commmand. Please try again.", hidden=True)

    return decorator
