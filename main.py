import logging
import os

from discord import Intents
from discord.ext import commands
from discord.ext.commands import CommandError, Context
from dotenv import load_dotenv

log = logging.getLogger(__name__)


class DamaBot(commands.Bot):

    def __init__(self, **kwargs):
        # Init client with all intents enabled
        kwargs["intents"] = Intents.all()
        super().__init__(command_prefix=os.environ["PREFIX"], **kwargs)

        self.load_extension("cogs.admin")
        self.load_extension("cogs.music")
        self.load_extension("cogs.emoji")
        # self.load_extension("cogs.scrobble")

    async def on_ready(self):
        log.info(f"Online as {self.user.name}. ID: {self.user.id}")

    async def on_command_error(self, ctx: Context, error: CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing argument '" + error.param.name + "'")
            return
        elif isinstance(error, CommandError):
            log.warning("Passing CommandError")
        else:
            log.error(f"Error during command: {ctx.message.clean_content}", exc_info=error)


def main():
    load_dotenv(verbose=True)

    setup_logging()

    bot = DamaBot()
    bot.run(os.environ["DISCORD_TOKEN"])


def setup_logging():
    _loglevel = os.environ["LOG_LEVEL"] if "LOG_LEVEL" in os.environ else "INFO"
    logging.basicConfig(level=_loglevel, format="%(levelname)-7s | %(asctime)s | %(name)-18s | %(message)s")
    logging.getLogger("discord").setLevel("INFO")


if __name__ == "__main__":
    main()
