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


async def split_message(text: str, ctx: Context, prefix="", suffix=""):
    chunk_len = 2000 - len(prefix) - len(suffix)
    messages_to_send = [prefix + text[idx: idx + chunk_len] + suffix for idx in range(0, len(text), chunk_len)]
    await ctx.reply(messages_to_send[0])
    [await ctx.send(msg) for msg in messages_to_send[1:]]


def get_command(ctx: Context) -> str:
    """
    Retrieve the original command as a string from a commands.Context or SlashContext.
    """
    if ctx.interaction:
        maybe_command = ctx.interaction.command()
        if isinstance(maybe_command, Command):
            return "/" + maybe_command.qualified_name

    # noinspection PyTypeChecker
    return ctx.message.clean_content
