from urllib.parse import quote_plus


def rym_search(query, searchtype=None):
    if searchtype:
        return f"https://rateyourmusic.com/search?searchterm={quote_plus(query)}&searchtype={searchtype}"
    else:
        return f"https://rateyourmusic.com/search?searchterm={quote_plus(query)}"


def mklinks(urls: dict) -> str:
    result = ""
    sep = ""
    for key in sorted(urls):
        result += f"{sep}[{key}]({urls[key]})"
        sep = " | "
    return result
