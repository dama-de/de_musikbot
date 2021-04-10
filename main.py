import json
import sys
import traceback
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
from discord.utils import find

from music import *
from music import search

bot = commands.Bot(command_prefix=os.environ["PREFIX"])

datadir = os.environ["DATA_DIR"] if "DATA_DIR" in os.environ else ""
datafile = os.path.join(datadir, "data.json")

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


@bot.group()
async def last(ctx):
    if not ctx.invoked_subcommand:
        await ctx.send("Try `{}help`".format(ctx.prefix))


@last.command()
async def register(ctx: discord.ext.commands.Context, lastfm_name):
    data["names"][str(ctx.author.id)] = lastfm_name
    await ctx.message.add_reaction(u'\U00002611')
    save()


@last.command()
async def now(ctx):
    author = ctx.author.display_name

    # Caching this reduces request count
    track = search.get_scrobble(get_lastfm_user(ctx.author))
    if not track:
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
    sp_result = await spotify_api.search(" ".join([track.artist.name, track.name, track.album.name]))
    if sp_result[0].items:
        sp_url = sp_result[0].items[0].external_urls["spotify"]
        sp_img = sp_result[0].items[0].album.images[0].url
        release_date = sp_result[0].items[0].album.release_date

        embed.description = "{} ({})".format(track.album.name, release_date[:4])
        embed.url = sp_url
        embed.set_thumbnail(url=sp_img)

    await ctx.send(embed=embed)


@last.command()
async def recent(ctx):
    lfmuser = lastfm_net.get_user(get_lastfm_user(ctx.author))
    recent_scrobbles = lfmuser.get_recent_tracks()

    embed = discord.Embed(title="Recent scrobbles")
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

    for i in range(len(recent_scrobbles)):
        scrobble = recent_scrobbles[i]
        embed.add_field(name=scrobble.track.title, value=scrobble.track.artist.name)

    await ctx.send(embed=embed)


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
    result = await spotify_api.search(search_query)
    url = result[0].items[0].external_urls["spotify"]
    await ctx.send(url)


@bot.command()
async def album(ctx, *, search_query=""):
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
    urls = dict()

    if not search_query and get_lastfm_user(ctx.author):
        scrobble = search.get_scrobble(get_lastfm_user(ctx.author))
        if scrobble:
            search_query = scrobble.artist.name

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


@bot.event
async def on_command_error(ctx, error):
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing argument '" + error.param.name + "'")


load()
save()

bot.run(os.environ["DISCORD_TOKEN"])
