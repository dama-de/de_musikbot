import logging
import os

from discord import Intents
from discord.ext import commands
from discord.ext.commands import CommandError, Context
from dotenv import load_dotenv

from util.config import Config

log = logging.getLogger(__name__)


def main():
    setup_logging()

    load_dotenv(verbose=True)

    bot = DamaBot()
    # https://discordpy.readthedocs.io/en/stable/logging.html
    bot.run(os.environ["DISCORD_TOKEN"], log_handler=None)


def setup_logging():
    _loglevel = os.environ["LOG_LEVEL"] if "LOG_LEVEL" in os.environ else "DEBUG"
    logging.basicConfig(level=_loglevel, format="%(levelname)-7s | %(asctime)s | %(name)-18s | %(message)s")
    logging.getLogger("discord").setLevel("INFO")
    logging.getLogger("pylast").setLevel("INFO")


class DamaBot(commands.Bot):

    def __init__(self, **kwargs):
        # Init client with all intents enabled
        kwargs["intents"] = Intents.all()
        super().__init__(command_prefix=os.environ["PREFIX"], **kwargs)

    async def setup_hook(self):
        config = Config("admin")

        # This should always be loaded, else we can't manage cogs at all
        await self.load_ext("cogs.admin")

        if "cogs.enabled" in config.data:
            for cog in config.data["cogs.enabled"]:
                await self.load_ext(cog)

    async def load_ext(self, cog: str):
        if cog not in self.extensions:
            log.info(f"Loading {cog}")
            await self.load_extension(cog)

    async def on_ready(self):
        log.info(f"Online as {self.user.name}. ID: {self.user.id}")

    async def on_command_error(self, ctx: Context, error: CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("Missing argument '" + error.param.name + "'")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.reply("Unknown command.")
        elif isinstance(error, CommandError):
            log.warning("Passing CommandError", error)
        else:
            log.error(f"Error during command: {ctx.message.clean_content}", exc_info=error)
        await super().on_command_error(ctx, error)


if __name__ == "__main__":
    main()
