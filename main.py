import discord
from discord.ext import commands
from discord.utils import find

from music import *

bot = commands.Bot(command_prefix=os.environ["PREFIX"])


@bot.event
async def on_ready():
    print("Online.")


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
    lfmuser = lastfm_net.get_user(data["names"][str(ctx.author.id)])

    # Caching this reduces request count
    now_playing = lfmuser.get_now_playing()

    artist = now_playing.get_artist().name
    track = now_playing.get_title(properly_capitalized=False)
    # tags = now_playing.get_album().get_top_tags()

    embed = discord.Embed(title="{} - {}".format(artist, track))
    embed.set_author(name=author, icon_url=ctx.author.avatar_url)
    embed.set_footer(text="Now scrobbling on last.fm")

    if now_playing.get_album():
        album = now_playing.get_album().get_title(properly_capitalized=False)
        img_url = now_playing.get_album().get_cover_image(pylast.SIZE_MEGA)
    else:
        album = ""
        img_url = None

    embed.description = album

    if img_url:
        embed.set_thumbnail(url=img_url)

    # Try to enhance with Spotify data
    sp_result = spotify_api.search(" ".join([artist, track, album]))
    if sp_result[0].items:
        sp_url = sp_result[0].items[0].external_urls["spotify"]
        sp_img = sp_result[0].items[0].album.images[0].url
        release_date = sp_result[0].items[0].album.release_date

        embed.description = "{} ({})".format(album, release_date[:4])
        embed.url = sp_url
        embed.set_thumbnail(url=sp_img)

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

col1_width = 22
col2_width = 22

tbl_format = "{:>2}|{:#.#}|{:$.$}|{:>4}\n".replace("#", str(col1_width)).replace("$", str(col2_width))
tbl_artist_format = "{:>2}|{:#.#}|{:>4}\n".replace("#", str(col1_width + col2_width + 1))


@last.command()
async def tracks(ctx, period="all"):
    if period not in periods:
        await ctx.send("Unknown time-period. Possible values: all, 7d, 1m, 3m, 6m, 12m")

    lfmuser = lastfm_net.get_user(data["names"][str(ctx.author.id)])
    top_tracks = lfmuser.get_top_tracks(period=periods[period], limit=10)

    embed = discord.Embed(title="Top tracks (" + period + ")")
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

    col_artists = [t.item.artist.name for t in top_tracks]
    col_titles = [t.item.title for t in top_tracks]
    col_scrobbles = [t.weight for t in top_tracks]

    description = "```\n"
    description += tbl_format.format("No", "Artist", "Title", "Scr.").replace(" ", "_")

    for i in range(len(col_artists)):
        description += tbl_format.format(i + 1, col_artists[i], col_titles[i], col_scrobbles[i])

    description += "```"
    embed.description = description

    await ctx.send(embed=embed)


@last.command()
async def albums(ctx, period="all"):
    if period not in periods:
        await ctx.send("Unknown time-period. Possible values: all, 7d, 1m, 3m, 6m, 12m")

    lfmuser = lastfm_net.get_user(data["names"][str(ctx.author.id)])
    top_albums = lfmuser.get_top_albums(period=periods[period], limit=10)

    embed = discord.Embed(title="Top albums (" + period + ")")
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

    col_artists = [t.item.artist.name for t in top_albums]
    col_titles = [t.item.title for t in top_albums]
    col_scrobbles = [t.weight for t in top_albums]

    description = "```\n"
    description += tbl_format.format("No", "Artist", "Album", "Scr.").replace(" ", "_")

    for i in range(len(col_artists)):
        description += tbl_format.format(i + 1, col_artists[i], col_titles[i], col_scrobbles[i])

    description += "```"
    embed.description = description

    await ctx.send(embed=embed)


@last.command()
async def artists(ctx, period="all"):
    if period not in periods:
        await ctx.send("Unknown time-period. Possible values: all, 7d, 1m, 3m, 6m, 12m")

    lfmuser = lastfm_net.get_user(data["names"][str(ctx.author.id)])
    top_artists = lfmuser.get_top_artists(period=periods[period], limit=10)

    embed = discord.Embed(title="Top artists (" + period + ")")
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

    col_artist = [t.item.name for t in top_artists]
    col_scrobbles = [t.weight for t in top_artists]

    description = "```\n"
    description += tbl_artist_format.format("No", "Artist", "Scr.").replace(" ", "_")

    for i in range(len(col_artist)):
        description += tbl_artist_format.format(i + 1, col_artist[i], col_scrobbles[i])

    description += "```"
    embed.description = description

    await ctx.send(embed=embed)


@bot.command()
async def track(ctx, *, search_query):
    result = spotify_api.search(search_query)
    url = result[0].items[0].external_urls["spotify"]
    await ctx.send(url)


@bot.command()
async def album(ctx, *, search_query):
    urls = dict()
    result = spotify_api.search(search_query, types=("album",))

    album = result[0].items[0]
    artist = ", ".join([a.name for a in album.artists])
    urls["Spotify"] = album.external_urls["spotify"]
    image = album.images[0].url
    year = album.release_date[:4]

    album_detail = spotify_api.album(album.id)

    full_length_ms = sum([t.duration_ms for t in album_detail.tracks.items])
    minutes = int(full_length_ms / 60_000)
    length = "{} min".format(minutes)

    urls["RYM"] = rym_search(album.name)

    description = f"{artist}\n\n{mklinks(urls)}"
    footer = "{} • {} songs, {}".format(year, album.total_tracks, length)

    embed = discord.Embed(title=album.name, description=description, url=urls["Spotify"])
    embed.set_footer(text=footer)
    embed.set_thumbnail(url=image)

    await ctx.send(embed=embed)


@bot.command()
async def artist(ctx, *, search_query):
    urls = dict()
    last_result = lastfm_net.search_for_artist(search_query).get_next_page()[0]

    artist = last_result.get_name(properly_capitalized=True)
    urls["Last.fm"] = last_result.get_url()
    bio = last_result.get_bio("summary").split("<a href")[0]
    top_tags = [t.item.name for t in last_result.get_top_tags(limit=6) if int(t.weight) >= 10]

    embed = discord.Embed()
    embed.title = artist
    description = "{}\n\nTop Tags: {}".format(bio, ", ".join(top_tags))

    sp_result = spotify_api.search(artist, types=("artist",), limit=1)
    if sp_result[0].items:
        # artist_id = sp_result[0].items[0].id
        # artist = sp_result[0].items[0].name
        # genres = ", ".join(sp_result[0].items[0].genres)
        # popularity = sp_result[0].items[0].popularity
        urls["Spotify"] = sp_result[0].items[0].external_urls["spotify"]
        img_url = sp_result[0].items[0].images[0].url
        embed.set_thumbnail(url=img_url)

    urls["RYM"] = rym_search(artist)

    description += f"\n\n{mklinks(urls)}"
    chosenkey = find(lambda key: key in urls, ["Spotify", "Last.fm", "RYM"])
    embed.url = urls[chosenkey]
    embed.description = description

    await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    print(error)
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing argument '" + error.param.name + "'")


load()
save()

bot.run(os.environ["DISCORD_TOKEN"])
