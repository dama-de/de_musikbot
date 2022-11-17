import logging

from discord.ext.commands import Bot, Cog, Context, command

_log = logging.getLogger(__name__)


async def setup(bot: Bot):
    await bot.add_cog(Admin())


class Admin(Cog):

    async def cog_check(self, ctx):
        return await ctx.bot.is_owner(ctx.author)

    @command(hidden=True)
    async def load(self, ctx: Context, cog: str):
        ctx.bot.load_extension(cog)
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @command(hidden=True)
    async def unload(self, ctx: Context, cog: str):
        ctx.bot.unload_extension(cog)
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @command(hidden=True)
    async def reload(self, ctx: Context, cog: str):
        ctx.bot.reload_extension(cog)
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @command(hidden=True)
    async def syncslash(self, ctx: Context):
        # await ctx.bot.slash.sync_all_commands(delete_from_unused_guilds=True, delete_perms_from_unused_guilds=True)
        await ctx.bot.tree.sync()
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @command(hidden=True)
    async def leave(self, ctx: Context, server_id=None):
        if not server_id:
            server_id = ctx.guild.id
        guild = ctx.bot.get_guild(server_id)
        await guild.leave()
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
