import discord
from datetime import datetime

days_in_a_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

def bool_emoji(val):
    return '✅' if val else '❌'


def ordinal(n):
    """
    Convert an integer into its ordinal representation::

        make_ordinal(0)   => '0th'
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'
    """
    n = int(n)
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix


def genitive(word):
    word = word.strip()
    return f"{word}'" if word.endswith('s') else f"{word}'s"


def map_values(val: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """
    maps a value in a range to another range
    """
    val = min(max(val, in_min), in_max)
    return (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def get_next_date(month, day, tz):
    now = datetime.now(tz=tz)
    try:
        birthday = datetime(year=now.year, month=month, day=day, tzinfo=tz)
    except ValueError:
        birthday = datetime(year=now.year, month=month + 1, day=1, tzinfo=tz)
    if birthday < now:
        birthday = datetime(year=now.year + 1, month=month, day=day, tzinfo=tz)
    return birthday


def validate_date_str(month: str | int, day: str | int):
    if not str(month).isdigit() or int(month) not in range(1, 13):
        return False, 'Invalid month, has to be a number between 1 and 12.'

    if not str(day).isdigit() or int(day) not in range(1, days_in_a_month[int(month)] + 1):
        return False, f'Invalid day for the specified month ({ordinal(int(day))} of {month_names[int(month)-1]}).'

    return True, None


def create_embed(title: str, author_field: tuple = None, content: str = None, embed_url: str = None,
                 image_url: str = None, footnote: str = None, color: discord.Color = None):
    """
    creates a Discord Embed with title, content, footer, etc.
    """

    embed = discord.Embed(title=title if title else None)
    embed.colour = color if color else discord.Color.random()

    if author_field:
        author_name, author_url, icon_url = author_field
        embed.set_author(name=author_name, url=author_url, icon_url=icon_url)

    if footnote:
        embed.set_footer(text=footnote)

    embed.description = content
    embed.url = embed_url
    if image_url:
        if image_url.split('.').pop().strip() in ['jpg', 'jpeg', 'gif', 'png']:
            embed.set_image(url=image_url)
    return embed
