'''
frequently used utils for the LotR-Trivia Bot
'''
import random
from datetime import datetime, timedelta

import asyncio
import discord


ordinal = lambda n: '%d%s' % (n, 'tsnrhtdd'[(n/10 % 10 != 1)*(n % 10 < 4)*n % 10::4])


def map_vals(val, in_min, in_max, out_min, out_max):
    '''
    maps a value in a range to another range
    '''
    val = min(max(val, in_min), in_max)
    return (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def create_embed(title=False, content=False, embed_url=False, link_url=False,
                 footnote=False, color=False, author_info=False):
    '''
    creates an Discord Embed with title, content, footer, etc.
    '''
    if title:
        embed = discord.Embed(title=title)
    else:
        embed = discord.Embed()
    if color:
        embed.color = discord.Color.from_rgb(
            int(color[0]),
            int(color[1]),
            int(color[2]))
    else:
        embed.color = discord.Color.from_rgb(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255))

    if author_info:
        author_name, avatar_url = author_info
        embed.set_author(name=author_name, icon_url=avatar_url)

    if footnote:
        embed.set_footer(text=footnote)

    if content:
        embed.description = content

    if embed_url:
        embed.url = embed_url
    if link_url:
        if link_url.split('.').pop().strip() in ['jpg', 'jpeg', 'gif', 'png']:
            embed.set_image(url=link_url)
    return embed


async def handle_ready_check(bot, ctx, player_count=0):

    # fetch the tagged user, exit conditions for bots / same user
    players = [ctx.channel.guild.get_member(ctx.author.id), *ctx.message.mentions]
    for player in players[1:][::-1]:
        if player.bot:
            await ctx.send(':x: {} is a bot, so you can\'t tag them.')
            players.remove(player)
        if player == ctx.author:
            await ctx.send(':x: You don\'t need to tag yourself.')
            players.remove(player)
    if player_count: # if fixed limit set
        if len(players) != player_count:
            await ctx.send(f':x: Please tag exactly {player_count-1} valid user{"s" if player_count-1 > 1 else ""}.')
            return (False, [])
    else:
        if len(players) < 2:
            await ctx.send(':x: You have to tag *at least* 1 valid user, not including yourself.')
            return (False, [])

    # initializing a list that tracks who is ready and who is not.
    ready_list = {player: 0 for player in players}
    # set the initiator to ready, HAS TO BE THE FIRST ELEMENT IN THE PLAYERS LIST
    ready_list[players[0]] = 1
    timeout = bot.config['discord']['ready_check_timeout']

    # func to creates / updates Ready Check
    async def manage_check_embed(ready_msg=None):
        ready_embed = discord.Embed()
        ready_count = 0
        for player, ready in ready_list.items():
            ready_embed.add_field(
                name=player.display_name, value=bot.config["discord"]["indicators"][ready])
            ready_count += ready
        ready_embed.description = f':stopwatch: Timeout in: {timeout//60}m,{timeout%60}s.'
        if all(ready for ready in ready_list.values()):
            ready_embed.title = f'Ready Check complete: {ready_count}/{len(players)} players ready.'
            ready_embed.set_footer(text='Send "Ready" to complete the Ready Check!')
        else:
            ready_embed.title = f':white_check_mark: Ready Check complete. {len(players)} players ready.'

        if ready_msg:
            await ready_msg.edit(embed=ready_embed)
        else:
            return await ctx.send(embed=ready_embed)

    # create the Ready Check Embed
    ready_msg = await manage_check_embed()

    # check function for the Ready Check, wraps manage_check_embed
    def ready_check(chk_msg):
        if chk_msg.author in players and chk_msg.content.lower() in ['ready','positive','yes','ye','yup']:
            ready_list[chk_msg.author] = 1
            return True
        return False

    deadline = datetime.now() + timedelta(seconds=timeout)
    try:
        while not all(ready for ready in ready_list.values()):
            await bot.wait_for('message', check=ready_check, timeout=(deadline - datetime.now()).seconds)
            await manage_check_embed(ready_msg)
            if (deadline - datetime.now()).seconds not in range(timeout):
                raise TimeoutError
        return (True, players)

    except (asyncio.TimeoutError, TimeoutError):
        await ctx.send(':x: Ready Check failed. Make sure your opponent is online and ready to battle.')
        return (False, [])
