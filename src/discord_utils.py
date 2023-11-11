"""
frequently used utils for the discord interface of the bot
"""
import asyncio
from datetime import datetime, timedelta

import discord
from discord.ext import commands

import backend_utils


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


async def handle_ready_check(cog, ctx, player_count=0):
    # fetch the tagged user, exit conditions for bots / same user
    players = [ctx.channel.guild.get_member(ctx.author.id), *ctx.message.mentions]
    for player in players[1:][::-1]:
        if player.bot:
            await ctx.send(':x: {} is a bot, so you can\'t tag them.')
            players.remove(player)
        if player == ctx.author:
            await ctx.send(':x: You don\'t need to tag yourself.')
            players.remove(player)
    if player_count:  # if fixed limit set
        if len(players) != player_count:
            await ctx.send(
                f':x: Please tag exactly {player_count - 1} valid user{"s" if player_count - 1 > 1 else ""}.')
            return False, []
    else:
        if len(players) < 2:
            await ctx.send(':x: You have to tag *at least* 1 valid user, not including yourself.')
            return False, []

    # initializing a list that is tracking who is ready and who is not.
    ready_list = {player: 0 for player in players}
    # set the initiator to ready, HAS TO BE THE FIRST ELEMENT IN THE PLAYERS LIST
    ready_list[players[0]] = 1
    timeout = cog.options['timeout']

    # func to creates / updates Ready Check
    async def manage_check_embed(ready_chk_msg=None):
        ready_embed = discord.Embed()
        ready_count = 0
        for ready_player, ready in ready_list.items():
            ready_embed.add_field(
                name=ready_player.display_name, value=backend_utils.bool_emoji(ready))
            ready_count += ready
        ready_embed.description = f':stopwatch: Timeout in: {timeout // 60}m,{timeout % 60}s.'
        if not all(ready for ready in ready_list.values()):
            ready_embed.title = f'Ready Check in progress: {ready_count}/{len(players)} players ready.'
            ready_embed.set_footer(text='Send "Ready" to complete the Ready Check!')
        else:
            ready_embed.title = f':white_check_mark: Ready Check complete. {len(players)} players ready.'

        if ready_chk_msg:
            await ready_chk_msg.edit(embed=ready_embed)
        else:
            return await ctx.send(embed=ready_embed)

    # create the Ready Check Embed
    ready_msg = await manage_check_embed()

    # check function for the Ready Check
    def ready_check(chk_msg):
        if chk_msg.author in players and chk_msg.content.lower() in ['ready', 'positive', 'yes', 'ye', 'yup']:
            ready_list[chk_msg.author] = 1
            return True
        return False

    deadline = datetime.now() + timedelta(seconds=timeout)
    try:
        while not all(ready for ready in ready_list.values()):
            await cog.bot.wait_for('message', check=ready_check, timeout=(deadline - datetime.now()).seconds)
            await manage_check_embed(ready_msg)
            if (deadline - datetime.now()).seconds not in range(timeout):
                raise TimeoutError
        return True, players

    except (asyncio.TimeoutError, TimeoutError):
        await ctx.send(':x: Ready Check failed. Make sure your opponent is online and ready to battle.')
        return False, []


def is_category_allowed(ctx, category, settings, defaults, logger):
    # return true if in a DM-channel
    if isinstance(ctx.channel, discord.channel.DMChannel):
        return 1
    # is there a channel-specific setting available?
    if ctx.channel.id in settings.keys():
        # check if the given category is defined
        if category in settings[ctx.channel.id].keys():
            return settings[ctx.channel.id][category]

    # is there a channel-specific setting available?
    if ctx.guild.id in settings.keys():
        # check if the given category is defined
        if category in settings[ctx.guild.id].keys():
            return settings[ctx.guild.id][category]

    # try to fetch the default value
    if category in defaults.keys():
        return defaults[category]

    # if everything fails, just allow it lol
    logger.error('Category "%s" not found, allowing it by default.', category)
    return 1


class CategoryNotAllowed(commands.CheckFailure):
    """
    custom error that is raised when the command used belongs to a disabled category
    """

    def __init__(self, category):
        self.category = category
        super().__init__()


class ChannelBusy(commands.CheckFailure):
    """
    custom error that is raised when the channel is currently busy
    """

    def __init__(self, message: discord.Message):
        self.orig_message = message
        super().__init__()


def category_check(category: str):
    """
    checks whether the given category is allowed in this context
    """

    async def predicate(ctx):
        if is_category_allowed(ctx, category, ctx.bot.caches['discord_settings'],
                               ctx.bot.options['discord']['settings']['defaults'],
                               ctx.bot.logger):
            return True
        else:
            raise CategoryNotAllowed(category)

    return commands.check(predicate)


def channel_busy_check():
    """
    checks whether the channel is currently busy
    """

    async def predicate(ctx):
        if ctx.channel.id in ctx.bot.busy_channels:
            raise ChannelBusy(ctx.message)
        else:
            return True

    return commands.check(predicate)
