from discord.ext.commands import Bot, Cog, Context, command


def setup(bot: Bot):
    bot.add_cog(Admin())


class Admin(Cog):

    async def cog_check(self, ctx):
        return await ctx.bot.is_owner(ctx.author)

    @command(hidden=True)
    async def load(self, ctx: Context, cog: str):
        ctx.bot.load_extension(cog)

    @command(hidden=True)
    async def unload(self, ctx: Context, cog: str):
        ctx.bot.unload_extension(cog)

    @command(hidden=True)
    async def reload(self, ctx: Context, cog: str):
        ctx.bot.reload_extension(cog)

    @command(hidden=True)
    async def syncslash(self, ctx: Context):
        await ctx.bot.slash.sync_all_commands(delete_from_unused_guilds=True, delete_perms_from_unused_guilds=True)
