import asyncio
import random

import discord
from discord.ext import commands

import backend_utils
import discord_utils as du
from template_cog import LotrCog


class QuoteBattle(LotrCog):
    """
    manages a quote-battle between two users
    """

    def __init__(self, bot):
        super().__init__(bot)

    @du.category_check('battles')
    @du.channel_busy_check()
    @commands.guild_only()
    @commands.command(name='quotebattle',
                      aliases=['qbattle', 'qb', 'quote-battle', 'quotefight', 'qfight', 'qf', 'battle'])
    async def quote_battle_handler(self, ctx):
        """
        starts a quote battle with subsequent voting
        """
        server = ctx.guild

        result, players = await du.handle_ready_check(self, ctx, player_count=2)

        if not result:
            return

        def quote_check(chk_msg):
            return chk_msg.channel == ctx.channel and chk_msg.author in players

        self.bot.busy_channels.append(ctx.channel.id)
        orig_rounds = self.options['rounds'] * 2
        rounds_left = orig_rounds - 1
        random.shuffle(players)
        act_player = players[0]
        first_round = True
        await ctx.send(
            f'Welcome to the epic quote battle between {players[0].mention} and {players[1].mention}!\n{act_player.nick if act_player.nick else act_player.display_name} starts! Prepare for battle!')

        while rounds_left > 0:
            try:
                msg = await self.bot.wait_for('message', check=quote_check,
                                              timeout=self.options['timeout'] // 2)
            except asyncio.TimeoutError:
                msg = await ctx.send(f'Careful {act_player.mention}, half of your time to respond has passed!',
                                     delete_after=30)
                try:
                    await self.bot.wait_for('message', check=quote_check,
                                            timeout=self.options['timeout'] // 2)
                except asyncio.TimeoutError:
                    await ctx.send('You did not answer in time. The battle ended.')
                    break

            if first_round:
                if msg.author.id == act_player.id:
                    first_round = False
                else:
                    await ctx.send(f'Hey, wait for {act_player.display_name} to start the battle!', delete_after=10)
                    await msg.delete()
                    continue

            if msg.author.id != act_player.id:
                rounds_left -= 1
                act_player = msg.author
                if rounds_left == orig_rounds // 2:
                    await ctx.send(f'Half-time! {rounds_left} rounds to go!')
                if rounds_left == 0:
                    await asyncio.sleep(60)

        if ctx.channel.id in self.bot.busy_channels:
            self.bot.busy_channels.remove(ctx.channel.id)

        msg_text = 'The quote battle between {} and {} ended.\n{} :one: for {} and :two: for {}'
        if server.id in self.options['voting_roles']:
            score_msg = await ctx.send(msg_text.format(players[0].display_name, players[1].display_name,
                                                       f"Hey <@&{self.options['voting_roles'][server.id]}>, vote",
                                                       players[0].mention, players[1].mention))
        else:
            score_msg = await ctx.send(
                msg_text.format(players[0].display_name, players[1].display_name, 'Vote', players[0].mention,
                                players[1].mention))

        await score_msg.add_reaction('1️⃣')  # number 1
        await score_msg.add_reaction('2️⃣')  # number 2
        await asyncio.sleep(self.options['voting_time'])

        try:
            # re-fetch message
            score_msg = await ctx.fetch_message(score_msg.id)
            await score_msg.add_reaction('🛑')  # stop-sign

            # remove bot reactions, and remove self-votes
            await score_msg.remove_reaction('1️⃣', server.me)
            try:
                await score_msg.remove_reaction('1️⃣', players[0])
            except discord.errors.NotFound:
                pass

            await score_msg.remove_reaction('2️⃣', server.me)
            try:
                await score_msg.remove_reaction('2️⃣', players[1])
            except discord.errors.NotFound:
                pass

            # re-fetch message again
            score_msg = await ctx.fetch_message(score_msg.id)

            voting = [0, 0]
            for item in score_msg.reactions:
                if item.emoji == '1️⃣':
                    voting[0] = item.count
                elif item.emoji == '2️⃣':
                    voting[1] = item.count

            ret_str = f'The vote for the battle between {players[0].mention} and {players[1].mention} concluded.\n'
            if voting[0] == voting[1]:
                await ctx.send(ret_str + 'Draw! Congratulations, both of you did well!')
            else:
                winner = voting[0] < voting[1]
                await ctx.send(
                    ret_str + f'{players[winner].mention} wins the quote battle {max(voting)}:{min(voting)}! What a fight!')

        except discord.errors.HTTPException:
            await ctx.send(backend_utils.bool_emoji(
                False) + ' An error occurred while counting the votes. Sorry for that. You can probably figure out who won yourself ;)')

    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def quoteday(self, ctx):
        state = ctx.message.content.split(' ')[-1].lower()

        if state == 'off' or state == 'stop':
            if ctx.guild.id in self.caches['quoteday']:
                del self.caches['quoteday'][ctx.guild.id]
            await ctx.send(':sunrise_over_mountains: Quoteday ended.')
        elif state == 'on' or state == 'start':
            self.caches['quoteday'][ctx.guild.id] = True
            await ctx.send(':tada: Quoteday started! Everyone now has to attach images to their messages!')
        elif state == 'quoteday':
            await ctx.send(
                f'Quoteday status for this server: {backend_utils.bool_emoji(self.caches["quoteday"].get(ctx.guild.id, False))}')
        else:
            await ctx.send('Invalid state, state can be on/off or start/stop.')

    @commands.Cog.listener('on_message')
    async def quoteday_listener(self, msg):
        if msg.author.bot or msg.embeds or msg.author.id in self.bot.blocked_users or not msg.guild:
            return

        if isinstance(msg.channel, discord.channel.DMChannel):
            return

        if msg.guild.id not in self.caches['quoteday']:
            return

        if not msg.channel.permissions_for(msg.channel.guild.me).manage_messages:
            return

        if du.is_category_allowed(msg, 'battles', self.bot.caches['discord_settings'],
                                  self.bot.options['discord']['settings']['defaults'],
                                  self.bot.logger):
            return

        valid = False
        extra_text = ''

        if msg.attachments:
            for file in msg.attachments:
                ext = file.filename.split('.')[-1].lower()
                if ext in self.options['image_extensions']:
                    valid = True
                else:
                    extra_text = f'The file `{file.filename}` was not recognized as an image. If you believe this is a mistake, please punch {self.bot.application.owner.mention} :)'

        if not valid:
            try:
                await msg.author.send(self.options['quoteday_reminder'].format(mention=msg.author.mention,
                                                                               link=self.options['quote_link'],
                                                                               delete_after=60))
                if extra_text:
                    await msg.author.send(extra_text, delete_after=60)
            except discord.errors.Forbidden:
                try:
                    await msg.channel.send(self.options['quoteday_reminder'].format(mention=msg.author.mention,
                                                                                    link=self.options['quote_link'],
                                                                                    delete_after=60))
                    if extra_text:
                        await msg.channel.send(extra_text, delete_after=60)
                except discord.errors.Forbidden:
                    pass
            await msg.delete()


async def setup(bot):
    await bot.add_cog(QuoteBattle(bot))
