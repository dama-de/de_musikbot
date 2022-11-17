from .scrobble import Scrobble


async def setup(bot):
    await bot.add_cog(Scrobble())
