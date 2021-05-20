import logging
import random
import asyncio
import discord
from discord.ext import commands
import cogs

class QuoteBattle(commands.Cog):
    '''
    Manages a quotebattle between two users
    '''
    def __init__(self,bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.', self.__class__.__name__.title())

    @commands.guild_only()
    @commands.command(name='quotebattle', aliases=['qbattle', 'qb', 'quote-battle', 'quotefight', 'qfight', 'qf'])
    async def quote_battle_handler(self, ctx):
        server = ctx.guild
        # perms_changed = []

        result, players = await cogs._dcutils.handle_ready_check(self.bot, ctx, player_count=2)

        if not result:
            return

        # for player in players:
        #     self.bot.blocked.append(player.id)
        #     if not ctx.channel.permissions_for(player).send_messages:
        #         perms_changed.append(player)
        #         await ctx.channel.set_permissions(player, send_messages=True, reason='Quote battle')

        def quote_check(msg):
            return msg.channel == ctx.channel and msg.author in players

        orig_rounds = self.bot.config['discord']['quote_battle']['rounds']*2
        rounds_left = orig_rounds-1
        random.shuffle(players)
        act_player = players[0]
        first_round = True
        await ctx.send('Welcome to the epic quote battle between {} and {}!\n{} starts! Prepare for battle!'.format(*(player.mention for player in players), act_player.display_name))

        while rounds_left > 0:
            try:
                msg = await self.bot.wait_for('message', check=quote_check, timeout=self.bot.config['discord']['quote_battle']['timeout']//2)
            except asyncio.TimeoutError:
                msg = await ctx.send('Careful both of you, half of your time to respond has passed!', delete_after=30)
                try:
                    await self.bot.wait_for('message', check=quote_check, timeout=self.bot.config['discord']['quote_battle']['timeout']//2)
                except asyncio.TimeoutError:
                    await ctx.send('You did not answer in time. The battle ended.')
                    break

            if first_round:
                if msg.author.id == act_player.id:
                    first_round = False
                else:
                    await ctx.send('Hey, wait for {} to start the battle!'.format(act_player.display_name), delete_after=10)
                    await msg.delete()
                    continue

            if msg.author.id != act_player.id:
                rounds_left -= 1
                act_player = msg.author
                if rounds_left == orig_rounds//2:
                    await ctx.send('Half-time! {} rounds to go!'.format(rounds_left))

        # for player in players:
        #     self.bot.blocked.remove(player.id)
        #     if player in perms_changed:
        #         await ctx.set_permissions(player, send_messages=False, reason='Quote battle')

        score_msg = await ctx.send(f'The quote battle between {players[0].display_name} and {players[1].display_name} ended.\nVote :one: for {players[0].mention} and :two: for {players[1].mention}')

        await score_msg.add_reaction('1️⃣') # number 1
        await score_msg.add_reaction('2️⃣') # number 2
        await asyncio.sleep(self.bot.config['discord']['quote_battle']['voting_time'])

        try:
            #refetch message
            score_msg = await ctx.fetch_message(score_msg.id)
            await score_msg.add_reaction('🛑') #stop-sign

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

            # refetch message again
            score_msg = await ctx.fetch_message(score_msg.id)

            voting = [0, 0]
            for item in score_msg.reactions:
                if item.emoji == '1️⃣':
                    voting[0] = item.count
                elif item.emoji == '2️⃣':
                    voting[1] = item.count

            ret_str = 'The vote for the battle between {} and {} concluded.\n'.format(*(player.mention for player in players))
            if voting[0] == voting[1]:
                await ctx.send(ret_str+'Draw! Congratulations, both of you did well!')
            else:
                winner = voting[0] < voting[1]
                await ctx.send(ret_str+f'{players[winner].mention} wins the quote battle! What a fight!')

        except discord.errors.HTTPException:
            await ctx.send(self.bot.config['discord']['indicators'][0] + ' An error occured while counting the votes. Sorry for that. You can probably figure out who won yourself ;)')


def setup(bot):
    bot.add_cog(QuoteBattle(bot))
