import asyncio
import copy
import logging
from typing import Optional, Literal, Collection, Union

import discord
import pylast
import tekore
from discord.app_commands import describe
from discord.ext.commands import Bot, Cog, CommandError, CommandInvokeError, Context, MissingRequiredArgument, \
    hybrid_command, hybrid_group

from util import get_command
from util.config import Config
from . import search
from .classes import Album, Artist, Track
from .search import genius, lastfm_net
from .util import get_activity, make_table, mklinks, rym_search, tbl_artist_format, tbl_format

# TODO Slash command error handler
# if "SKIP_SLASH" not in os.environ:
#     @Cog.listener()
#     async def on_slash_command_error(self, ctx: SlashContext, error: Exception):
#         if isinstance(error, discord.NotFound) and error.code == 10062:
#             # NotFound with code 10062 means that the interaction timed out before we sent a response
#             _log.warning("Interaction timed out: " + get_command(ctx))
#             return
#
#         # Forward the exception to the regular error handler
#         await self.cog_command_error(ctx, CommandInvokeError(error))

slash_guilds = None

_log = logging.getLogger(__name__)


def is_slash(ctx: Context):
    return ctx.interaction


class NotRegisteredError(Exception):
    def __init__(self, user: discord.User):
        self.user = user


class Music(Cog):
    def __init__(self, bot: Bot):
        self._bot = bot

        self.config = Config("music")
        self.data = self.config.data

        if not self.data:
            self.data["names"] = {}
            self.config.save()

    def get_lastfm_user(self, user: Union[discord.User, discord.Member]) -> Optional[str]:
        if str(user.id) in self.data["names"]:
            return self.data["names"][str(user.id)]
        raise NotRegisteredError(user)

    def get_guild_lastfm_users(self, guild: discord.Guild) -> Collection[discord.Member]:
        return [u for u in guild.members if str(u.id) in self.data["names"]]

    async def reply_on_error(self, ctx: Context, message: str):
        if is_slash(ctx):
            await ctx.send(message, ephemeral=True)
        else:
            await ctx.reply(message)
        return

    async def cog_command_error(self, ctx: Context, error: CommandError):
        """
        We use this method to handle the most common errors in the cog, so it doesn't have to be
        done for each command separately. It will be called automatically from discord.py.
        """
        if isinstance(error, CommandInvokeError):
            # Unpack the original error for further handling
            error = error.original

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
        elif isinstance(error, NotRegisteredError):
            await self.reply_on_error(ctx, "You must register with `/last register` first.")
        else:
            _log.error("Unhandled error during command: " + get_command(ctx), exc_info=error)
            await self.reply_on_error(ctx, "There was an unknown error, please contact the bot owner.")

    # ---------- Regular commands ----------
    @hybrid_group()
    async def last(self, ctx: Context):
        """last.fm command category"""
        if not ctx.invoked_subcommand:
            await ctx.send("Try `{}help`".format(ctx.prefix))

    @last.command()
    async def register(self, ctx: Context, lastfm_name: str):
        """Register your last.fm account with this bot."""
        if not await search.user_exists(lastfm_name):
            await self.reply_on_error(ctx, "User does not exist.")
            return

        self.data["names"][str(ctx.author.id)] = lastfm_name
        self.config.save()
        if is_slash(ctx):
            await ctx.send("Done.", ephemeral=True)
        else:
            await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @last.command()
    async def now(self, ctx: Context):
        """Fetch the currently playing song."""
        author = ctx.author.display_name

        track = Track()

        # Try to retrieve the user's activity
        activity = get_activity(ctx.author, "Spotify")
        if activity:
            track.update(search._pack_spotify_activity(activity))

        if not activity:
            # Get current scrobble from last.fm, skip if activity was used
            track.update(await search.get_scrobble(self.get_lastfm_user(ctx.author)))
            if not track:
                await self.reply_on_error(ctx, "Nothing is currently scrobbling on last.fm")
                return

        # Try to enhance with Spotify data
        sp_query = f"track:{track.name} artist:{track.artist.name}"
        sp_query += f" album:{track.album.name}" if track.album else ""
        sp_result = await search.search_spotify_track(sp_query)
        if sp_result:
            track.update(sp_result)

        embed = discord.Embed(title="{} - {}".format(track.artist.name, track.name), url=track.url)
        embed.set_author(name=author, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=track.album.img_url or None)

        # Footer text, depending on where we got our data from
        footer_string = "Now playing on Spotify" if activity else "Now scrobbling on last.fm"
        embed.set_footer(text=footer_string)

        # If an album date exists, mention the year in the description, else suppress
        formatted_year = f" ({track.album.date[:4]})" if track.album.date else ""
        embed.description = track.album.name + formatted_year

        await ctx.send(embed=embed)

    @last.command()
    async def recent(self, ctx: Context):
        """Fetch your last scrobbles."""
        recent_scrobbles = await search.get_recent(self.get_lastfm_user(ctx.author))

        embed = discord.Embed(title="Recent scrobbles")
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)

        for i in range(len(recent_scrobbles)):
            scrobble = recent_scrobbles[i]
            embed.add_field(name=scrobble.track.title, value=scrobble.track.artist.name)

        await ctx.send(embed=embed)

    # Possible chart timeframes
    periods = {"all": pylast.PERIOD_OVERALL,
               "7d": pylast.PERIOD_7DAYS,
               "1m": pylast.PERIOD_1MONTH,
               "3m": pylast.PERIOD_3MONTHS,
               "6m": pylast.PERIOD_6MONTHS,
               "12m": pylast.PERIOD_12MONTHS}

    @last.command()
    async def tracks(self, ctx: Context, period: Literal["all", "7d", "1m", "3m", "6m", "12m"] = "all"):
        """Fetch your most played tracks.
        Time periods: all, 7d, 1m, 3m, 6m, 12m"""
        if period not in self.periods:
            await self.reply_on_error(ctx, "Unknown time-period. Possible values: all, 7d, 1m, 3m, 6m, 12m")
            return

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
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)

        await ctx.send(embed=embed)

    @last.command()
    async def albums(self, ctx: Context, period: Literal["all", "7d", "1m", "3m", "6m", "12m"] = "all"):
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
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)

        await ctx.send(embed=embed)

    @last.command()
    async def artists(self, ctx: Context, period: Literal["all", "7d", "1m", "3m", "6m", "12m"] = "all"):
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
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)

        await ctx.send(embed=embed)

    @last.command()
    async def my(self, ctx: discord.ext.commands.Context):
        """Share your last.fm profile link"""
        last_username = self.get_lastfm_user(ctx.author)
        await ctx.reply(f"https://www.last.fm/user/{last_username}")

    @hybrid_command()
    async def track(self, ctx: Context, *, search_query: str):
        """Search for a single track"""
        result = await search.search_spotify_track(search_query)

        if not result:
            await self.reply_on_error(ctx, "No results found.")
            return

        url = result.url
        await ctx.send(url)

    @hybrid_command()
    async def album(self, ctx: Context, *, search_query=""):
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
        embed.set_thumbnail(url=album.img_url or None)

        await ctx.send(embed=embed)

    @hybrid_command()
    async def artist(self, ctx: Context, *, search_query=""):
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

        if not last_result:
            await self.reply_on_error(ctx, "No artist found.")
            return

        artist.update(last_result)
        urls["Last.fm"] = last_result.url

        sp_result = await search.search_spotify_artist(last_result.name)
        if sp_result:
            artist.update(sp_result)
            urls["Spotify"] = sp_result.url

        urls["RYM"] = rym_search(artist.name, searchtype="a")

        embed = discord.Embed(title=artist.name, url=artist.url)
        embed.set_thumbnail(url=artist.img_url or None)
        embed.description = f"{artist.bio}\n\nTop Tags: {artist.tags}\n\n{mklinks(urls)}"

        await ctx.send(embed=embed)

    @hybrid_command(description="Search for a Genius page, or get the page of the song you're listening to")
    @describe(search_query="Title and artist of the song")
    async def lyricsgenius(self, ctx: Context, search_query: str = None):
        async with ctx.typing():
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

    # @app_command(description="Create a custom chart")
    # async def chart(self, ctx: Context, search_by: Literal["artist", "album"], search_query: str = None, user: Member = None):

    @hybrid_command(description="See who has the most plays of a track, album, or artist", aliases=["wk"])
    async def who_knows(self, ctx: Context, type: Literal["artist", "album", "track"], *, search_query: str = None):
        async with ctx.typing():
            lastfm_user = self.get_lastfm_user(ctx.author)
            subject: Union[Album, Artist, Track]

            # Use the current scrobble if no search was submitted
            scrobble = None
            if not search_query:
                scrobble = await search.get_scrobble(lastfm_user)
                if not scrobble:
                    await self.reply_on_error(ctx, "Nothing is currently scrobbling.")
                    return

            if type == "artist":
                subject = scrobble.artist if scrobble else await search.search_lastfm_artist(search_query)
                title = subject.name
            elif type == "album":
                subject = scrobble.album if scrobble else await search.search_lastfm_album(search_query)
                title = f"{subject.artist.name} - {subject.name}"
            elif type == "track":
                subject = scrobble if scrobble else await search.search_lastfm_track(search_query)
                title = f"{subject.name} - {subject.artist.name}"

            async def get_playcount_for_member(lfm: Union[pylast.Track, pylast.Album, pylast.Artist],
                                               member: discord.Member):
                lfm = copy.copy(lfm)
                lfm.username = self.get_lastfm_user(member)
                playcount = await asyncio.to_thread(lfm.get_userplaycount)
                return member, playcount

            coros = []
            for member in self.get_guild_lastfm_users(ctx.guild):
                coros.append(get_playcount_for_member(subject.origin, member))
            results = {member: playcount for member, playcount in await asyncio.gather(*coros)}
            # Exclude 0 plays
            filtered_results = filter(lambda r: r[1] > 0, results.items())
            # Sort by playcount
            sorted_results = sorted(filtered_results, key=lambda i: i[1], reverse=True)

            embed = discord.Embed(title=title, url=subject.url)
            embed.description = "\n".join([f"{r[0].display_name}: {r[1]}" for r in sorted_results])
            await ctx.send(embed=embed)
