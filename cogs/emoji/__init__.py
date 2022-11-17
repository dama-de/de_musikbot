import logging
import unicodedata
import re

import aiohttp
from discord.ext import commands
from discord.ext.commands import Bot, Cog, Context

_log = logging.getLogger(__name__)


async def setup(bot: Bot):
    await bot.add_cog(Emoji())


class Emoji(Cog):

    @commands.command()
    async def emoji(self, ctx: Context, emoji):
        await ctx.reply(unicodedata.name(emoji[0]))

    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.command()
    async def yoink(self, ctx: Context, emoji: str, name=""):
        match = re.match("^<a?:(.+):(\\d+)>$", emoji)

        if match:
            name = match.group(1) if not name else name
            emoji_id = match.group(2)
        else:
            match = re.match("^https://cdn\\.discordapp\\.com/emojis/(\\d+)\\..*$", emoji)

            if not match:
                await ctx.reply("Please supply an emoji or a link to one.")
                return
            elif match and not name:
                await ctx.reply("Please supply a name with an emoji-link.")
                return

            emoji_id = match.group(1)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://cdn.discordapp.com/emojis/{emoji_id}") as resp:
                data = await resp.read()

        if not data:
            await ctx.reply("Could not fetch the emoji image.")
            return

        emoji = await ctx.guild.create_custom_emoji(name=name, image=data)
        await ctx.reply(str(emoji))
