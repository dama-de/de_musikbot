from typing import Optional
from urllib.parse import quote_plus

from discord import User, Member, Activity
from discord.utils import get


def get_activity(user: User, of_type: str) -> Optional[Activity]:
    member: Member = None

    if isinstance(user, Member):
        member = user
    if isinstance(user, User):
        # Try to find the user as a member, so we can see their activities
        if user.mutual_guilds:
            member = get(user.mutual_guilds[0].members, id=user.id)

    if member:
        if of_type:
            return get(member.activities, name=of_type)
        else:
            return member.activity


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
