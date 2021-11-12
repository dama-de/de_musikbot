from .scrobble import Scrobble


def setup(bot):
    bot.add_cog(Scrobble())
