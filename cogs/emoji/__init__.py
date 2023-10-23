import io
import logging
import re
from urllib.parse import urlparse

import aiohttp
import unicodedata
from PIL import Image
from discord.ext import commands
from discord.ext.commands import Bot, Cog, Context
from discord.utils import find

_log = logging.getLogger(__name__)


async def setup(bot: Bot):
    await bot.add_cog(Emoji())


class Emoji(Cog):
    PATTERN_DISCORD_EMOJI_MARKUP = re.compile("^<a?:(.+):(\\d+)>$")
    PATTERN_DISCORD_EMOJI_URL = re.compile("^https://cdn\\.discordapp\\.com/emojis/(\\d+)\\..*$")
    TEMPLATE_DISCORD_EMOJI_URL = "https://cdn.discordapp.com/emojis/"

    @commands.command(hidden=True)
    async def pyemoji(self, ctx: Context, emoji):
        await ctx.reply(unicodedata.name(emoji[0]))

    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.cooldown(1, 5)  # Global rate-limit
    @commands.command()
    async def yoink(self, ctx: Context, emoji: str, name=""):
        url = None
        if match := re.match(Emoji.PATTERN_DISCORD_EMOJI_MARKUP, emoji):
            name = match.group(1) if not name else name
            url = Emoji.TEMPLATE_DISCORD_EMOJI_URL + match.group(2)

        elif match := re.match(Emoji.PATTERN_DISCORD_EMOJI_URL, emoji):
            url = Emoji.TEMPLATE_DISCORD_EMOJI_URL + match.group(1)

        elif (url_match := urlparse(emoji)) \
                and url_match.scheme in ["http", "https"] \
                and url_match.netloc:
            url = url_match.geturl()

        if not name:
            await ctx.reply("Please supply a name.")
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if not resp.content_type.startswith("image/"):
                    await ctx.reply("URL must point to an image file!")
                    return
                elif resp.content_length > 1024 ** 2:
                    await ctx.reply("File must be 1 MB or smaller!")
                    return
                data = await resp.read()

        if not data:
            await ctx.reply("Could not fetch the emoji image.")
            return

        try:
            with Image.open(io.BytesIO(data), formats=["jpeg", "png", "gif", "webp"]) as img:
                converted = io.BytesIO()
                if img.is_animated and img.format != "gif":
                    img.save(converted, "gif", save_all=True, disposal=2)
                elif img.format not in ["jpeg", "png"]:
                    img.save(converted, "png")
                else:
                    converted.write(data)
        except Exception:
            await ctx.reply("Error during image processing.")
            return

        try:
            emoji = await ctx.guild.create_custom_emoji(name=name, image=converted.getvalue())
            await ctx.reply(str(emoji))
        except Exception as e:
            await ctx.reply(str(e))

    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.command()
    async def yeet(self, ctx: Context, emoji: str):
        if match := re.match(Emoji.PATTERN_DISCORD_EMOJI_MARKUP, emoji):
            found_emoji = find(lambda e: e.id == int(match.group(2)), ctx.guild.emojis)
            if found_emoji:
                await found_emoji.delete()
                await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
