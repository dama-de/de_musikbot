import discord
import json
import pylast
import tekore as tk
from dotenv import load_dotenv
import os
from discord.ext import commands


load_dotenv(verbose=True)

lastfm_icon = "https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/196_Lastfm_Square_logo_logos-512.png"

datadir = os.environ["DATA_DIR"] if "DATA_DIR" in os.environ else ""
datafile = os.path.join(datadir, "data.json")
data = {"names": {"132551667085344769": "dam4rusxp"}}

bot = commands.Bot(command_prefix='$')


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


@bot.group()
async def last(ctx):
    pass


@last.command()
async def register(ctx: discord.ext.commands.Context, lastfm_name):
    data["names"][str(ctx.author.id)] = lastfm_name
    await ctx.message.add_reaction(u'\U00002611')
    save()


@last.command()
async def now(ctx):
    author = ctx.author.display_name
    lfmuser = lastfm_net.get_user(data["names"][str(ctx.author.id)])

    # Caching this reduces request count
    now_playing = lfmuser.get_now_playing()

    artist = now_playing.get_artist().name
    track = now_playing.get_title(properly_capitalized=False)
    album = now_playing.get_album().get_title(properly_capitalized=False)
    # tags = now_playing.get_album().get_top_tags()

    sp_result = spotify_api.search(" ".join([artist, track, album]))
    sp_url = sp_result[0].items[0].external_urls["spotify"]
    sp_img = sp_result[0].items[0].album.images[0].url
    release_date = sp_result[0].items[0].album.release_date

    title = "{} - {}".format(artist, track)
    description = "{} ({})".format(album, release_date[:4])
    embed = discord.Embed(title=title, description=description, url=sp_url)
    embed.set_author(name=author, icon_url=ctx.author.avatar_url)
    embed.set_thumbnail(url=sp_img)
    embed.set_footer(text="Now scrobbling on last.fm",
                     icon_url=lastfm_icon)
    await ctx.send(embed=embed)


@last.command()
async def recent(ctx):
    lfmuser = lastfm_net.get_user(data["names"][str(ctx.author.id)])
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


@last.command()
async def tracks(ctx, period="all"):
    if period not in periods:
        await ctx.send("Unknown time-period. Possible values: all, 7d, 1m, 3m, 6m, 12m")

    lfmuser = lastfm_net.get_user(data["names"][str(ctx.author.id)])
    top_tracks = lfmuser.get_top_tracks(period=periods[period], limit=10)

    embed = discord.Embed(title="Top tracks (" + period + ")")
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

    embed.add_field(name="Artist", value="\n".join([t.item.artist.name[:28] for t in top_tracks]))
    embed.add_field(name="Title", value="\n".join([t.item.title[:28] for t in top_tracks]))
    embed.add_field(name="Scrobbles", value="\n".join([str(t.weight) for t in top_tracks]))

    await ctx.send(embed=embed)


@last.command()
async def albums(ctx, period="all"):
    if period not in periods:
        await ctx.send("Unknown time-period. Possible values: all, 7d, 1m, 3m, 6m, 12m")

    lfmuser = lastfm_net.get_user(data["names"][str(ctx.author.id)])
    top_albums = lfmuser.get_top_albums(period=periods[period], limit=10)

    embed = discord.Embed(title="Top albums (" + period + ")")
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

    embed.add_field(name="Artist", value="\n".join([t.item.artist.name[:28] for t in top_albums]))
    embed.add_field(name="Title", value="\n".join([t.item.title[:28] for t in top_albums]))
    embed.add_field(name="Scrobbles", value="\n".join([str(t.weight) for t in top_albums]))

    await ctx.send(embed=embed)


@last.command()
async def artists(ctx, period="all"):
    if period not in periods:
        await ctx.send("Unknown time-period. Possible values: all, 7d, 1m, 3m, 6m, 12m")

    lfmuser = lastfm_net.get_user(data["names"][str(ctx.author.id)])
    top_artists = lfmuser.get_top_artists(period=periods[period], limit=10)

    embed = discord.Embed(title="Top artists (" + period + ")")
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

    embed.add_field(name="Artist", value="\n".join([t.item.name[:50] for t in top_artists]))
    embed.add_field(name="Scrobbles", value="\n".join([str(t.weight) for t in top_artists]))

    await ctx.send(embed=embed)


@bot.command()
async def track(ctx, *, search_query):
    result = spotify_api.search(search_query)
    url = result[0].items[0].external_urls["spotify"]
    await ctx.send(url)


@bot.command()
async def album(ctx, *, search_query):
    result = spotify_api.search(search_query, types=("album",))

    album = result[0].items[0]
    artist = ", ".join([a.name for a in album.artists])
    url = album.external_urls["spotify"]
    image = album.images[0].url
    year = album.release_date[:4]

    album_detail = spotify_api.album(album.id)
    full_length_ms = sum([t.duration_ms for t in album_detail.tracks.items])
    minutes = int(full_length_ms / 60_000)

    length = "{} min".format(minutes)
    description = "{} • {} songs, {}".format(year, album.total_tracks, length)
    embed = discord.Embed(title=album.name, description=artist, url=url)
    embed.set_footer(text=description)
    embed.set_thumbnail(url=image)
    await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    print(error)
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing argument '" + error.param.name + "'")

API_KEY = os.environ["LAST_API_KEY"]
API_SECRET = os.environ["LAST_API_SECRET"]
lastfm_net = pylast.LastFMNetwork(
    api_key=API_KEY,
    api_secret=API_SECRET
)

CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
spotify_api = tk.Spotify(tk.request_client_token(CLIENT_ID, CLIENT_SECRET))

load()
save()

bot.run(os.environ["DISCORD_TOKEN"])
