import logging

from discord import ApplicationContext
from discord.ext.commands import Context

_log = logging.getLogger(__name__)


def get_command(ctx) -> str:
    """
    Retrieve the original command as a string from a commands.Context or SlashContext.
    """
    if isinstance(ctx, Context):
        return ctx.message.clean_content()
    elif isinstance(ctx, ApplicationContext):
        result = "/" + ctx.command.qualified_name
        # result += " " + ctx.subcommand_name if ctx.command.is_subcommand else ""
        # result += " " + " ".join([f"{k}:{v}" for (k, v) in ctx.options.items()])
        return result
