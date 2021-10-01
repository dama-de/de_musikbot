import asyncio
import logging
from typing import Optional

import discord
import pylast
import tekore
from discord.embeds import EmptyEmbed
from discord.ext.commands import MissingRequiredArgument, Bot, Cog, command, group
from discord_slash import SlashContext, cog_ext, SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option

from util import auto_defer, get_command
from util.config import Config
from . import search
from .classes import Album, Artist
from .search import lastfm_net, genius
from .util import rym_search, mklinks, make_table, tbl_format, tbl_artist_format

slash_guilds = None

_log = logging.getLogger(__name__)


class Music(Cog):
    def __init__(self, bot: Bot):
        self._bot = bot

        self.config = Config("music")
        self.data = self.config.data

        if not self.data:
            self.data["names"] = {"132551667085344769": "dam4rusxp"}
            self.config.save()

    def get_lastfm_user(self, user: discord.User) -> Optional[str]:
        if str(user.id) in self.data["names"]:
            return self.data["names"][str(user.id)]
        return None

    async def reply_on_error(self, ctx, message: str):
        if isinstance(ctx, SlashContext):
            await ctx.send(message, hidden=True)
        else:
            await ctx.reply(message)
        return

    async def cog_command_error(self, ctx, error):
        """
        We use this method to handle the most common errors in the cog, so it doesn't have to be
        done for each command separately. It will be called automatically from discord.py.
        """
        if isinstance(error, pylast.PyLastError):
            _log.warning("Last.fm did not respond on time.")
            await self.reply_on_error(
                ctx, "There was an error while communicating with the Last.fm API, please try again later."
            )
        elif isinstance(error, tekore.HTTPError):
            _log.warning("Spotify did not respond on time.")
            await self.reply_on_error(
                ctx, "There was an error while communicating with the Spotify API, please try again later."
            )
        else:
            _log.error("Unhandled error during command: " + get_command(ctx), exc_info=error)
            await self.reply_on_error(
                ctx, "There was an unknown error, please contact the bot owner."
            )

    @Cog.listener()
    async def on_slash_command_error(self, ctx: SlashContext, error: Exception):
        if isinstance(error, discord.NotFound) and error.code == 10062:
            # NotFound with code 10062 means that the interaction timed out before we sent a response
            _log.warning("Interaction timed out: " + get_command(ctx))
            return

        # Forward the exception to the regular error handler
        await self.cog_command_error(ctx, error)

    # ---------- Regular commands ----------
    @group()
    async def last(self, ctx):
        """last.fm command category"""
        if not ctx.invoked_subcommand:
            await ctx.send("Try `{}help`".format(ctx.prefix))

    @last.command()
    async def register(self, ctx, lastfm_name: str):
        """Register your last.fm account with this bot."""
        self.data["names"][str(ctx.author.id)] = lastfm_name
        self.config.save()
        if isinstance(ctx, SlashContext):
            await ctx.send("Done.", hidden=True)
        else:
            await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @last.command()
    async def now(self, ctx):
        """Fetch the currently playing song."""
        author = ctx.author.display_name

        # Caching this reduces request count
        track = await search.get_scrobble(self.get_lastfm_user(ctx.author))
        if not track:
            await self.reply_on_error(ctx, "Nothing is currently scrobbling on last.fm")
            return

        # Try to enhance with Spotify data
        sp_result = await search.search_spotify_track(" ".join([track.artist.name, track.name, track.album.name]))
        if sp_result:
            track.update(sp_result)

        embed = discord.Embed(title="{} - {}".format(track.artist.name, track.name), url=track.url)
        embed.set_author(name=author, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="Now scrobbling on last.fm")
        embed.set_thumbnail(url=track.album.img_url or EmptyEmbed)

        # If an album date exists, mention the year in the description, else suppress
        formatted_year = f" ({track.album.date[:4]})" if track.album.date else ""
        embed.description = track.album.name + formatted_year

        await ctx.send(embed=embed)

    @last.command()
    async def recent(self, ctx):
        """Fetch your last scrobbles."""
        lfmuser = lastfm_net.get_user(self.get_lastfm_user(ctx.author))
        recent_scrobbles = lfmuser.get_recent_tracks()

        embed = discord.Embed(title="Recent scrobbles")
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        for i in range(len(recent_scrobbles)):
            scrobble = recent_scrobbles[i]
            embed.add_field(name=scrobble.track.title, value=scrobble.track.artist.name)

        await ctx.send(embed=embed)

    # Constants for markdown table generation
    periods = {"all": pylast.PERIOD_OVERALL,
               "7d": pylast.PERIOD_7DAYS,
               "1m": pylast.PERIOD_1MONTH,
               "3m": pylast.PERIOD_3MONTHS,
               "6m": pylast.PERIOD_6MONTHS,
               "12m": pylast.PERIOD_12MONTHS}

    @last.command()
    async def tracks(self, ctx, period="all"):
        """Fetch your most played tracks.
        Time periods: all, 7d, 1m, 3m, 6m, 12m"""
        if period not in self.periods:
            await self.reply_on_error(ctx, "Unknown time-period. Possible values: all, 7d, 1m, 3m, 6m, 12m")

        lfmuser = lastfm_net.get_user(self.get_lastfm_user(ctx.author))
        top_tracks = lfmuser.get_top_tracks(period=self.periods[period], limit=10)

        cols = {
            "No": range(1, len(top_tracks) + 1),
            "Artist": [t.item.artist.name for t in top_tracks],
            "Title": [t.item.title for t in top_tracks],
            "Scr.": [t.weight for t in top_tracks]
        }

        embed = discord.Embed(title="Top tracks (" + period + ")")
        embed.description = make_table(tbl_format, cols)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @last.command()
    async def albums(self, ctx, period="all"):
        """Fetch your most played albums.
        Time periods: all, 7d, 1m, 3m, 6m, 12m"""
        if period not in self.periods:
            await self.reply_on_error(ctx, "Unknown time-period. Possible values: all, 7d, 1m, 3m, 6m, 12m")

        lfmuser = lastfm_net.get_user(self.get_lastfm_user(ctx.author))
        top_albums = lfmuser.get_top_albums(period=self.periods[period], limit=10)

        cols = {
            "No": range(1, len(top_albums) + 1),
            "Artist": [t.item.artist.name for t in top_albums],
            "Album": [t.item.title for t in top_albums],
            "Scr.": [t.weight for t in top_albums]
        }

        embed = discord.Embed(title="Top albums (" + period + ")")
        embed.description = make_table(tbl_format, cols)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @last.command()
    async def artists(self, ctx, period="all"):
        """Fetch your most played artists.
        Time periods: all, 7d, 1m, 3m, 6m, 12m"""
        if period not in self.periods:
            await self.reply_on_error(ctx, "Unknown time-period. Possible values: all, 7d, 1m, 3m, 6m, 12m")

        lfmuser = lastfm_net.get_user(self.get_lastfm_user(ctx.author))
        top_artists = lfmuser.get_top_artists(period=self.periods[period], limit=10)

        cols = {
            "No": range(1, len(top_artists) + 1),
            "Artist": [t.item.name for t in top_artists],
            "Scr.": [t.weight for t in top_artists]
        }

        embed = discord.Embed(title="Top artists (" + period + ")")
        embed.description = make_table(tbl_artist_format, cols)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @command()
    async def track(self, ctx, *, search_query: str):
        """Search for a single track"""
        result = await search.search_spotify_track(search_query)
        url = result.url
        await ctx.send(url)

    @command()
    async def album(self, ctx, *, search_query=""):
        """Search for an album"""
        urls = dict()
        album = Album()

        # If no search query was supplied, try to fetch an album from the current scrobble,
        # and build the search from its artist and title
        last_album = None
        if not search_query and self.get_lastfm_user(ctx.author):
            scrobble = await search.get_scrobble(self.get_lastfm_user(ctx.author))
            if scrobble and scrobble.album:
                last_album = scrobble.album
                search_query = f"{scrobble.artist.name} {scrobble.album.name}"

        if not search_query:
            raise MissingRequiredArgument(ctx.command.params["search_query"])

        if not last_album:
            last_album = await search.search_lastfm_album(search_query)
        album.update(last_album)
        urls["Last.fm"] = last_album.url

        spotify_album = await search.search_spotify_album(search_query, extended=True)
        if spotify_album:
            album.update(spotify_album)
            urls["Spotify"] = spotify_album.url

        metrics = ""
        if album.date:
            year = album.date[:4]
            minutes = int(album.length / 60_000)
            metrics = f"\n{year} • {album.tracks} songs, {minutes} min"

        urls["RYM"] = rym_search(album.name, searchtype="l")
        description = f"*{album.artist.name}*{metrics}\n\n{mklinks(urls)}"

        embed = discord.Embed(title=album.name, description=description, url=album.url)
        embed.set_thumbnail(url=album.img_url or EmptyEmbed)

        await ctx.send(embed=embed)

    @command()
    async def artist(self, ctx, *, search_query=""):
        """Search for an artist"""
        urls = dict()
        artist = Artist()

        # If no search query was supplied, get the artist from the current scrobble and use its name as search
        if not search_query and self.get_lastfm_user(ctx.author):
            scrobble = await search.get_scrobble(self.get_lastfm_user(ctx.author))
            if scrobble:
                search_query = f"'{scrobble.artist.name}'"

        if not search_query:
            raise MissingRequiredArgument(ctx.command.params["search_query"])

        # Use exact search if the "query is in quotes" or 'in quotes'
        quotes = ['"', "'"]
        if search_query[0] in quotes and search_query[-1] in quotes and search_query[0] == search_query[-1]:
            last_result = await search.search_lastfm_artist(search_query[1:-1], exact=True)
        else:
            last_result = await search.search_lastfm_artist(search_query)
        artist.update(last_result)
        urls["Last.fm"] = last_result.url

        sp_result = await search.search_spotify_artist(last_result.name)
        if sp_result:
            artist.update(sp_result)
            urls["Spotify"] = sp_result.url

        urls["RYM"] = rym_search(artist.name, searchtype="a")

        embed = discord.Embed(title=artist.name, url=artist.url)
        embed.set_thumbnail(url=artist.img_url or EmptyEmbed)
        embed.description = f"{artist.bio}\n\nTop Tags: {artist.tags}\n\n{mklinks(urls)}"

        await ctx.send(embed=embed)

    # ---------- Slash Commands ----------
    @cog_ext.cog_slash(name="album", description="Search for an album",
                       options=[create_option(
                           name="search_query", description="name of the album", required=False,
                           option_type=SlashCommandOptionType.STRING)])
    @auto_defer
    async def _album(self, ctx: SlashContext, search_query=""):
        await self.album(ctx, search_query=search_query)

    @cog_ext.cog_slash(name="artist", description="Search for an artist",
                       options=[create_option(
                           name="search_query", description="name of the artist", required=False,
                           option_type=SlashCommandOptionType.STRING)])
    @auto_defer
    async def _artist(self, ctx: SlashContext, search_query=""):
        await self.artist(ctx, search_query=search_query)

    @cog_ext.cog_slash(name="track", description="Search for a track",
                       options=[create_option(
                           name="search_query", description="name of the track", required=False,
                           option_type=SlashCommandOptionType.STRING)])
    @auto_defer
    async def _track(self, ctx: SlashContext, search_query=""):
        await self.track(ctx, search_query=search_query)

    @cog_ext.cog_subcommand(base="last", name="register", description="Register your last.fm account with the bot",
                            options=[create_option(
                                name="lastfm_name", description="Your last.fm username", required=True,
                                option_type=SlashCommandOptionType.STRING)])
    async def _register(self, ctx: SlashContext, lastfm_name):
        await self.register(ctx, lastfm_name)

    @cog_ext.cog_subcommand(base="last", name="now", description="Fetch the currently playing song",
                            guild_ids=slash_guilds)
    @auto_defer
    async def _now(self, ctx: SlashContext):
        await self.now(ctx)

    @cog_ext.cog_subcommand(base="last", name="recent", description="Fetch your last 10 scrobbles",
                            guild_ids=slash_guilds)
    @auto_defer
    async def _recent(self, ctx: SlashContext):
        await self.recent(ctx)

    @cog_ext.cog_subcommand(base="last", name="artists", description="Fetch your most played artists",
                            options=[create_option(
                                name="period", description="Time period", required=False,
                                option_type=SlashCommandOptionType.STRING,
                                choices=["all", "7d", "1m", "3m", "6m", "12m"])])
    @auto_defer
    async def _artists(self, ctx: SlashContext, period="all"):
        await self.artists(ctx, period)

    @cog_ext.cog_subcommand(base="last", name="albums", description="Fetch your most played albums",
                            options=[create_option(
                                name="period", description="Time period", required=False,
                                option_type=SlashCommandOptionType.STRING,
                                choices=["all", "7d", "1m", "3m", "6m", "12m"])])
    @auto_defer
    async def _albums(self, ctx: SlashContext, period="all"):
        await self.albums(ctx, period)

    @cog_ext.cog_subcommand(base="last", name="tracks", description="Fetch your most played tracks",
                            options=[create_option(
                                name="period", description="Time period", required=False,
                                option_type=SlashCommandOptionType.STRING,
                                choices=["all", "7d", "1m", "3m", "6m", "12m"])])
    @auto_defer
    async def _tracks(self, ctx: SlashContext, period="all"):
        await self.tracks(ctx, period)

    @cog_ext.cog_slash(name="lyricsgenius",
                       description="Search for a Genius page, or get the page of the Song your're listening to",
                       guild_ids=slash_guilds,
                       options=[create_option(
                           name="search_query", description="Title and artist of the song", required=False,
                           option_type=SlashCommandOptionType.STRING
                       )])
    @auto_defer
    async def _lyrics(self, ctx: SlashContext, search_query=None):
        # Use the current scrobble if no search was submitted
        if not search_query:
            scrobble = await search.get_scrobble(self.get_lastfm_user(ctx.author))
            if not scrobble:
                await self.reply_on_error(ctx, "Nothing is currently scrobbling.")
                return
            search_query = f"{scrobble.name} {scrobble.artist.name}"

        song = await asyncio.to_thread(genius.search_song, title=search_query, get_full_info=False)

        if not song:
            await self.reply_on_error(ctx, f"Could not find '{search_query}' on Genius.")
            return

        embed = discord.Embed(title='Genius Lyrics')
        embed.add_field(name='Link', value=str(song.url))
        embed.set_thumbnail(url=song.header_image_url)
        await ctx.send(embed=embed)
