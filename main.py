import logging
import os
import sys
import traceback

from discord.ext import commands
from discord_slash import SlashCommand
from dotenv import load_dotenv

log = logging.getLogger(__name__)


class DamaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=os.environ["PREFIX"])
        self.load_extension("cogs.admin")
        self.load_extension("cogs.music")

    async def on_ready(self):
        log.info(f"Online as {self.user.name}. ID: {self.user.id}")

    async def on_command_error(self, ctx, error):
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing argument '" + error.param.name + "'")


def main():
    load_dotenv(verbose=True)

    _loglevel = os.environ["LOG_LEVEL"] if "LOG_LEVEL" in os.environ else "INFO"
    logging.basicConfig(level=_loglevel, format="%(levelname)-5s | %(asctime)s | %(name)-18s | %(message)s")

    bot = DamaBot()
    slash = SlashCommand(bot)

    bot.run(os.environ["DISCORD_TOKEN"])


if __name__ == "__main__":
    main()
