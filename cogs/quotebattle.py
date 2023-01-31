import asyncio
import random

import discord
from discord.ext import commands

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
    @commands.command(name='quotebattle', aliases=['qbattle', 'qb', 'quote-battle', 'quotefight', 'qfight', 'qf'])
    async def quote_battle_handler(self, ctx):
        """
        starts a quote battle with subsequent voting
        """
        server = ctx.guild
        # perms_changed = []

        result, players = await du.handle_ready_check(self.bot, ctx, player_count=2)

        if not result:
            return

        # for player in players:
        #     self.bot.blocked.append(player.id)
        #     if not ctx.channel.permissions_for(player).send_messages:
        #         perms_changed.append(player)
        #         await ctx.channel.set_permissions(player, send_messages=True, reason='Quote battle')

        def quote_check(chk_msg):
            return chk_msg.channel == ctx.channel and chk_msg.author in players

        self.bot.busy_channels.append(ctx.channel.id)
        orig_rounds = self.bot.config['discord']['quote_battle']['rounds'] * 2
        rounds_left = orig_rounds - 1
        random.shuffle(players)
        act_player = players[0]
        first_round = True
        await ctx.send(
            f'Welcome to the epic quote battle between {players[0].mention} and {players[1].mention}!\n{act_player.display_name} starts! Prepare for battle!')

        while rounds_left > 0:
            try:
                msg = await self.bot.wait_for('message', check=quote_check,
                                              timeout=self.bot.config['discord']['quote_battle']['timeout'] // 2)
            except asyncio.TimeoutError:
                msg = await ctx.send('Careful both of you, half of your time to respond has passed!', delete_after=30)
                try:
                    await self.bot.wait_for('message', check=quote_check,
                                            timeout=self.bot.config['discord']['quote_battle']['timeout'] // 2)
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

        # for player in players:
        #     self.bot.blocked.remove(player.id)
        #     if player in perms_changed:
        #         await ctx.set_permissions(player, send_messages=False, reason='Quote battle')
        if ctx.channel.id in self.bot.busy_channels:
            self.bot.busy_channels.remove(ctx.channel.id)

        msg_text = 'The quote battle between {} and {} ended.\n{} :one: for {} and :two: for {}'
        if server.id in self.bot.config['discord']['quote_battle']['voting_roles']:
            score_msg = await ctx.send(msg_text.format(players[0].display_name, players[1].display_name,
                                                       f"Hey <@&{self.bot.config['discord']['quote_battle']['voting_roles'][server.id]}>, vote",
                                                       players[0].mention, players[1].mention))
        else:
            score_msg = await ctx.send(
                msg_text.format(players[0].display_name, players[1].display_name, 'Vote', players[0].mention,
                                players[1].mention))

        await score_msg.add_reaction('1️⃣')  # number 1
        await score_msg.add_reaction('2️⃣')  # number 2
        await asyncio.sleep(self.bot.config['discord']['quote_battle']['voting_time'])

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
                await ctx.send(ret_str + f'{players[winner].mention} wins the quote battle! What a fight!')

        except discord.errors.HTTPException:
            await ctx.send(self.bot.config['discord']['indicators'][
                               0] + ' An error occurred while counting the votes. Sorry for that. You can probably figure out who won yourself ;)')


async def setup(bot):
    await bot.add_cog(QuoteBattle(bot))
