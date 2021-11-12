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


# Constants for markdown table generation
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
