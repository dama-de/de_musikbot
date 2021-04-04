import os
from urllib.parse import quote_plus

import pylast
import tekore as tk
from dotenv import load_dotenv

load_dotenv(verbose=True)

lastfm_net = pylast.LastFMNetwork(api_key=(os.environ["LAST_API_KEY"]), api_secret=(os.environ["LAST_API_SECRET"]))
spotify_api = tk.Spotify(
    tk.request_client_token(os.environ["SPOTIFY_CLIENT_ID"], os.environ["SPOTIFY_CLIENT_SECRET"]),
    asynchronous=True)


def rym_search(query):
    return "https://rateyourmusic.com/search?searchterm={}".format(quote_plus(query))


def mklinks(urls: dict) -> str:
    result = ""
    sep = ""
    for key in sorted(urls):
        result += f"{sep}[{key}]({urls[key]})"
        sep = " | "
    return result
