import json
import sys
import traceback
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
from discord.utils import find
from discord_slash import SlashCommand, SlashCommandOptionType, SlashContext
from discord_slash.utils.manage_commands import create_option

from music import *
from music import search

import lyricsgenius

genius = lyricsgenius.Genius(os.environ["GENIUS_CLIENT_SECRET"])

bot = commands.Bot(command_prefix=os.environ["PREFIX"])
slash = SlashCommand(bot, sync_commands=True)

datadir = os.environ["DATA_DIR"] if "DATA_DIR" in os.environ else ""
datafile = os.path.join(datadir, "data.json")

# Set your server id here to update slash commands without delay while debugging
# slash_guilds = [822951335191904267]
slash_guilds = None

data = {"names": {"132551667085344769": "dam4rusxp"}}


def save():
    global data
    with open(datafile, "w") as file:
        file.write(json.dumps(data))
        file.close()


def load():
    global data
    if os.path.exists(os.path.join(datadir, "data.json")):
        with open(datafile, "r") as file:
            data = json.loads(file.read())


def get_lastfm_user(user: discord.User) -> Optional[str]:
    if str(user.id) in data["names"]:
        return data["names"][str(user.id)]
    return None


@bot.event
async def on_ready():
    print(f"Online. Loaded {len(data['names'])} names.")


@bot.event
async def on_command_error(ctx, error):
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing argument '" + error.param.name + "'")


# ---------- Regular commands ----------
@bot.group()
async def last(ctx):
    """last.fm command category"""
    if not ctx.invoked_subcommand:
        await ctx.send("Try `{}help`".format(ctx.prefix))


@last.command()
async def register(ctx: discord.ext.commands.Context, lastfm_name):
    """Register your last.fm account with this bot."""
    data["names"][str(ctx.author.id)] = lastfm_name
    save()
    if isinstance(ctx, SlashContext):
        await ctx.send("Done.", hidden=True)
    else:
        await ctx.message.add_reaction(u'\U00002611')


@last.command()
async def now(ctx):
    """Fetch the currently playing song."""
    author = ctx.author.display_name

    # Caching this reduces request count
    track = search.get_scrobble(get_lastfm_user(ctx.author))
    if not track:
        if isinstance(ctx, SlashContext):
            await ctx.send("Nothing is currently scrobbling on last.fm", hidden=True)
        else:
            await ctx.reply("Nothing is currently scrobbling on last.fm")
        return

    embed = discord.Embed(title="{} - {}".format(track.artist.name, track.name))
    embed.set_author(name=author, icon_url=ctx.author.avatar_url)
    embed.set_footer(text="Now scrobbling on last.fm")
    embed.url = track.url

    if track.album:
        embed.description = track.album.name

    if track.album.img_url:
        embed.set_thumbnail(url=track.album.img_url)

    # Try to enhance with Spotify data
    sp_result = await search.search_spotify_track(" ".join([track.artist.name, track.name, track.album.name]))
    if sp_result:
        embed.url = sp_result.url
        embed.set_thumbnail(url=sp_result.album.img_url)
        embed.description = "{} ({})".format(track.album.name, sp_result.album.date[:4])

    await ctx.send(embed=embed)


@last.command()
async def recent(ctx):
    """Fetch your last scrobbles."""
    lfmuser = lastfm_net.get_user(get_lastfm_user(ctx.author))
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

col1_width = 22
col2_width = 22

tbl_format = "{:>2}|{:#.#}|{:$.$}|{:>4}\n".replace("#", str(col1_width)).replace("$", str(col2_width))
tbl_artist_format = "{:>2}|{:#.#}|{:>4}\n".replace("#", str(col1_width + col2_width + 1))


def make_table(format_string, cols: dict):
    table = "```\n"
    table += format_string.format(*cols.keys()).replace(" ", "_")

    for items in zip(*cols.values()):
        table += format_string.format(*items)

    table += "```"
    return table


@last.command()
async def tracks(ctx, period="all"):
    """Fetch your most played tracks.
    Time periods: all, 7d, 1m, 3m, 6m, 12m"""
    if period not in periods:
        await ctx.send("Unknown time-period. Possible values: all, 7d, 1m, 3m, 6m, 12m")

    lfmuser = lastfm_net.get_user(get_lastfm_user(ctx.author))
    top_tracks = lfmuser.get_top_tracks(period=periods[period], limit=10)

    cols = {
        "No": range(1, len(top_tracks) + 1),
        "Artist": [t.item.artist.name for t in top_tracks],
        "Title": [t.item.title for t in top_tracks],
        "Scr.": [t.weight for t in top_tracks]
    }

    description = make_table(tbl_format, cols)

    embed = discord.Embed(title="Top tracks (" + period + ")", description=description)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

    await ctx.send(embed=embed)


@last.command()
async def albums(ctx, period="all"):
    """Fetch your most played albums.
    Time periods: all, 7d, 1m, 3m, 6m, 12m"""
    if period not in periods:
        await ctx.send("Unknown time-period. Possible values: all, 7d, 1m, 3m, 6m, 12m")

    lfmuser = lastfm_net.get_user(get_lastfm_user(ctx.author))
    top_albums = lfmuser.get_top_albums(period=periods[period], limit=10)

    cols = {
        "No": range(1, len(top_albums) + 1),
        "Artist": [t.item.artist.name for t in top_albums],
        "Album": [t.item.title for t in top_albums],
        "Scr.": [t.weight for t in top_albums]
    }

    description = make_table(tbl_format, cols)

    embed = discord.Embed(title="Top albums (" + period + ")", description=description)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

    await ctx.send(embed=embed)


@last.command()
async def artists(ctx, period="all"):
    """Fetch your most played artists.
    Time periods: all, 7d, 1m, 3m, 6m, 12m"""
    if period not in periods:
        await ctx.send("Unknown time-period. Possible values: all, 7d, 1m, 3m, 6m, 12m")

    lfmuser = lastfm_net.get_user(get_lastfm_user(ctx.author))
    top_artists = lfmuser.get_top_artists(period=periods[period], limit=10)

    cols = {
        "No": range(1, len(top_artists) + 1),
        "Artist": [t.item.name for t in top_artists],
        "Scr.": [t.weight for t in top_artists]
    }

    description = make_table(tbl_artist_format, cols)

    embed = discord.Embed(title="Top artists (" + period + ")", description=description)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

    await ctx.send(embed=embed)


@bot.command()
async def track(ctx, *, search_query):
    """Search for a single track"""
    result = await search.search_spotify_track(search_query)
    url = result.url
    await ctx.send(url)


@bot.command()
async def album(ctx, *, search_query=""):
    """Search for an album"""
    urls = dict()

    if not search_query and get_lastfm_user(ctx.author):
        scrobble = search.get_scrobble(get_lastfm_user(ctx.author))
        if scrobble and scrobble.album:
            search_query = f"{scrobble.artist.name} {scrobble.album.name}"

    if not search_query:
        raise MissingRequiredArgument(ctx.command.params["search_query"])

    result = await search.search_spotify_album(search_query, extended=True)

    if not result:
        return

    urls["Spotify"] = result.url
    year = result.date[:4]
    minutes = int(result.length / 60_000)

    urls["RYM"] = rym_search(result.name, searchtype="l")

    metrics = "{} • {} songs, {} min".format(year, result.tracks, minutes)
    description = f"*{result.artist.name}*\n{metrics}\n\n{mklinks(urls)}"

    embed = discord.Embed(title=result.name, description=description, url=urls["Spotify"])
    embed.set_thumbnail(url=result.img_url)

    await ctx.send(embed=embed)


@bot.command()
async def artist(ctx, *, search_query=""):
    """Search for an artist"""
    urls = dict()

    if not search_query and get_lastfm_user(ctx.author):
        scrobble = search.get_scrobble(get_lastfm_user(ctx.author))
        if scrobble:
            search_query = f"'{scrobble.artist.name}'"

    if not search_query:
        raise MissingRequiredArgument(ctx.command.params["search_query"])

    # Use exact search if the "query is in quotes" or 'in quotes'
    quotes = ['"', "'"]
    if search_query[0] in quotes and search_query[-1] in quotes and search_query[0] == search_query[-1]:
        last_result = search.search_lastfm_artist(search_query[1:-1], exact=True)
    else:
        last_result = search.search_lastfm_artist(search_query)

    embed = discord.Embed()
    embed.title = last_result.name
    description = "{}\n\nTop Tags: {}".format(last_result.bio, last_result.tags)

    sp_result = await search.search_spotify_artist(last_result.name)
    if sp_result:
        urls["Spotify"] = sp_result.url
        embed.set_thumbnail(url=sp_result.img_url)

    urls["Last.fm"] = last_result.url
    urls["RYM"] = rym_search(last_result.name, searchtype="a")

    description += f"\n\n{mklinks(urls)}"
    chosenkey = find(lambda key: key in urls, ["Spotify", "Last.fm", "RYM"])
    embed.url = urls[chosenkey]
    embed.description = description

    await ctx.send(embed=embed)


# ---------- Slash Commands ----------
@slash.slash(name="album", description="Search for an album", guild_ids=slash_guilds,
             options=[create_option(
                 name="search_query", description="name of the album", required=False,
                 option_type=SlashCommandOptionType.STRING)])
async def _album(ctx, search_query=""):
    await album(ctx, search_query=search_query)


@slash.slash(name="artist", description="Search for an artist", guild_ids=slash_guilds,
             options=[create_option(
                 name="search_query", description="name of the artist", required=False,
                 option_type=SlashCommandOptionType.STRING)])
async def _artist(ctx, search_query=""):
    await artist(ctx, search_query=search_query)


@slash.slash(name="track", description="Search for a track", guild_ids=slash_guilds,
             options=[create_option(
                 name="search_query", description="name of the track", required=False,
                 option_type=SlashCommandOptionType.STRING)])
async def _track(ctx, search_query=""):
    await track(ctx, search_query=search_query)


@slash.slash(name="last", guild_ids=slash_guilds)
async def _last(ctx):
    pass


@slash.subcommand(base="last", name="register", description="Register your last.fm account with the bot",
                  guild_ids=slash_guilds,
                  options=[create_option(
                      name="lastfm_name", description="Your last.fm username", required=True,
                      option_type=SlashCommandOptionType.STRING)])
async def _register(ctx, lastfm_name):
    await register(ctx, lastfm_name)


@slash.subcommand(base="last", name="now", description="Fetch the currently playing song", guild_ids=slash_guilds)
async def _now(ctx):
    await now(ctx)


@slash.subcommand(base="last", name="recent", description="Fetch your last 10 scrobbles", guild_ids=slash_guilds)
async def _recent(ctx):
    await recent(ctx)


@slash.subcommand(base="last", name="artists", description="Fetch your most played artists", guild_ids=slash_guilds,
                  options=[create_option(
                      name="period", description="Time period", required=False,
                      option_type=SlashCommandOptionType.STRING,
                      choices=["all", "7d", "1m", "3m", "6m", "12m"])])
async def _artists(ctx, period="all"):
    await artists(ctx, period)


@slash.subcommand(base="last", name="albums", description="Fetch your most played albums", guild_ids=slash_guilds,
                  options=[create_option(
                      name="period", description="Time period", required=False,
                      option_type=SlashCommandOptionType.STRING,
                      choices=["all", "7d", "1m", "3m", "6m", "12m"])])
async def _albums(ctx, period="all"):
    await albums(ctx, period)


@slash.subcommand(base="last", name="tracks", description="Fetch your most played tracks", guild_ids=slash_guilds,
                  options=[create_option(
                      name="period", description="Time period", required=False,
                      option_type=SlashCommandOptionType.STRING,
                      choices=["all", "7d", "1m", "3m", "6m", "12m"])])
async def _tracks(ctx, period="all"):
    await tracks(ctx, period)


@slash.slash(name="lyricsGenius", description="Gets the Genius link for the song you're currently listening to", guild_ids=slash_guilds)
async def _lyrics(ctx):
    track = search.get_scrobble(get_lastfm_user(ctx.author))
    song = genius.search_song(title=str(track), artist=str(track.artist.name))
    lyrics = str(song.url)
    embed = discord.Embed(title='Genius Lyrics')
    embed.add_field(name='Link', value=str(song.url))
    embed.set_thumbnail(url=track.album.img_url)
    await ctx.send(embed=embed)

load()
save()

bot.run(os.environ["DISCORD_TOKEN"])

