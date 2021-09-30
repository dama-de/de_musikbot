import logging
import os

from discord.ext.commands import Context

if "SKIP_SLASH" not in os.environ:
    from discord_slash import SlashContext

_log = logging.getLogger(__name__)


def get_command(ctx) -> str:
    """
    Retrieve the original command as a string from a commands.Context or SlashContext.
    """
    if isinstance(ctx, Context):
        return ctx.message.clean_content
    elif isinstance(ctx, SlashContext):
        result = "/" + ctx.command
        result += " " + ctx.subcommand_name if ctx.subcommand_name else ""
        result += " " + " ".join([f"{k}:{v}" for (k, v) in ctx.kwargs.items()])
        return result
