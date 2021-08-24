import asyncio
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
        await func(*args, **kwargs)

    return decorator
