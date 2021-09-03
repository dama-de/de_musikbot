import logging
import os

from discord.ext import commands
from discord.ext.commands import CommandError, Context
from discord_slash import SlashCommand
from dotenv import load_dotenv

log = logging.getLogger(__name__)


class DamaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=os.environ["PREFIX"])

    async def on_ready(self):
        self.load_extension("cogs.admin")
        self.load_extension("cogs.music")
        log.info(f"Online as {self.user.name}. ID: {self.user.id}")

    async def on_command_error(self, ctx: Context, error: CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing argument '" + error.param.name + "'")
            return

        log.error(f"Error during command: {ctx.message.clean_content}", exc_info=error)


def main():
    load_dotenv(verbose=True)

    _loglevel = os.environ["LOG_LEVEL"] if "LOG_LEVEL" in os.environ else "INFO"
    logging.basicConfig(level=_loglevel, format="%(levelname)-5s | %(asctime)s | %(name)-18s | %(message)s")

    bot = DamaBot()
    slash = SlashCommand(bot)

    bot.run(os.environ["DISCORD_TOKEN"])


if __name__ == "__main__":
    main()
