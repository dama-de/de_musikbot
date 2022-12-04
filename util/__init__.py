import logging

from discord.app_commands import Command
from discord.ext.commands import Context

_log = logging.getLogger(__name__)


# TODO Printing a slash command
# elif isinstance(ctx, SlashContext):
#     result = "/" + ctx.command
#     result += " " + ctx.subcommand_name if ctx.subcommand_name else ""
#     result += " " + " ".join([f"{k}:{v}" for (k, v) in ctx.kwargs.items()])
#     return result


def get_command(ctx: Context) -> str:
    """
    Retrieve the original command as a string from a commands.Context or SlashContext.
    """
    if ctx.interaction:
        maybe_command = ctx.interaction.command()
        if isinstance(maybe_command, Command):
            return "/" + maybe_command.qualified_name
    return ctx.message.clean_content()
