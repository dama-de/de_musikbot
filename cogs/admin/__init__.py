import asyncio
import importlib.util
import json
import logging

from discord import Guild
from discord.ext.commands import Bot, Cog, Context, command

from util.config import Config

_log = logging.getLogger(__name__)


async def setup(bot: Bot):
    await bot.add_cog(Admin())


class Admin(Cog):

    def __init__(self):
        self.config = None

    async def cog_load(self) -> None:
        self.config = Config("admin")

        if "cogs.enabled" not in self.config.data:
            self.config.data["cogs.enabled"] = []

        self._save()

    async def cog_unload(self) -> None:
        self._save()

    async def cog_check(self, ctx: Context):
        return await ctx.bot.is_owner(ctx.author)

    def _save(self) -> None:
        self.config.data["cogs.enabled"] = list(set(self.config.data["cogs.enabled"]))
        self.config.save()

    @command(hidden=True)
    async def listcogs(self, ctx: Context):
        await ctx.reply("\n".join(sorted(ctx.bot.extensions)))

    @command(hidden=True)
    async def listenabled(self, ctx: Context):
        await ctx.reply("\n".join(sorted(self.config.data["cogs.enabled"])))

    @command(hidden=True)
    async def load(self, ctx: Context, cog: str):
        if not cog.startswith("cogs."):
            cog = "cogs." + cog

        resolved = importlib.util.find_spec(cog, None)
        if resolved:
            await ctx.bot.load_extension(cog)
            await self._react_ok(ctx)
        else:
            await ctx.message.add_reaction("\N{BLACK QUESTION MARK ORNAMENT}")

    @command(hidden=True)
    async def unload(self, ctx: Context, cog: str):
        if not cog.startswith("cogs."):
            cog = "cogs." + cog

        resolved = importlib.util.find_spec(cog, None)
        if resolved:
            await ctx.bot.unload_extension(cog)
            await self._react_ok(ctx)
        else:
            await ctx.message.add_reaction("\N{BLACK QUESTION MARK ORNAMENT}")

    @command(aliases=["r"], hidden=True)
    async def reload(self, ctx: Context, cog: str):
        if not cog.startswith("cogs."):
            cog = "cogs." + cog

        resolved = importlib.util.find_spec(cog, None)
        if resolved:
            await ctx.bot.reload_extension(cog)
            await self._react_ok(ctx)
        else:
            await ctx.message.add_reaction("\N{BLACK QUESTION MARK ORNAMENT}")

    @command(hidden=True)
    async def enable(self, ctx: Context, cog: str):
        if not cog.startswith("cogs."):
            cog = "cogs." + cog

        resolved = importlib.util.find_spec(cog, None)
        if resolved:
            if cog not in self.config.data:
                self.config.data["cogs.enabled"].append(cog)
                self._save()

            await self._react_ok(ctx)
        else:
            await ctx.message.add_reaction("\N{BLACK QUESTION MARK ORNAMENT}")

    @command(hidden=True)
    async def disable(self, ctx: Context, cog: str):
        if not cog.startswith("cogs."):
            cog = "cogs." + cog

        if cog in ctx.bot.extensions:
            self.config.data["cogs.enabled"].remove(cog)
            self._save()
            await self._react_ok(ctx)
        else:
            await ctx.message.add_reaction("\N{BLACK QUESTION MARK ORNAMENT}")

    @command(hidden=True)
    async def syncslash(self, ctx: Context):
        await ctx.bot.tree.sync()
        await self._react_ok(ctx)

    @command(hidden=True)
    async def clearslash(self, ctx: Context, guild: Guild = None):
        async with ctx.typing():
            commands = await ctx.bot.tree.fetch_commands(guild=guild)
            await asyncio.wait([appcommand.delete() for appcommand in commands])

        await self._react_ok(ctx)

    @command(hidden=True)
    async def leave(self, ctx: Context, server_id: int = None):
        if not server_id:
            server_id = ctx.guild.id
        guild = ctx.bot.get_guild(server_id)
        await guild.leave()
        await self._react_ok(ctx)

    @command(hidden=True)
    async def get(self, ctx: Context, config: str, item: str = None):
        conf = Config(config)
        if item:
            msg = f"`{json.dumps({item: conf.data[item]})}`"
        else:
            msg = f"```\n{json.dumps(conf.data, indent=4)}\n```"
        await ctx.reply(msg)

    @command(hidden=True)
    async def set(self, ctx: Context, config: str, item: str, value: str):
        conf = Config(config)
        conf.data[item] = value
        conf.save()
        await self._react_ok(ctx)

    async def _react_ok(self, ctx: Context):
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
