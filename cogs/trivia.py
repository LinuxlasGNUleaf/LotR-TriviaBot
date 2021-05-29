'''
Trivia cog for the LotR-Trivia Bot
'''
import asyncio
import csv
from io import BytesIO
import math
import logging
import random
import matplotlib.pyplot as plt
import numpy as np
import discord
from discord.ext import commands
import cogs._dcutils

plt.rcdefaults()

class Trivia(commands.Cog):
    '''
    handles the LotR-Trivia integration for the bot, including profile / scoreboards
    '''

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.reply = (lambda won, author, text='': self.bot.config['discord']['indicators'][won] + ' ' + random.choice(
            self.bot.config['discord']['compliments'] if won else self.bot.config['discord']['insults']).format(author.display_name) + text)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.',
                         self.__class__.__name__.title())

    @commands.command(name='profile')
    async def display_profile(self, ctx):
        '''
        creates a profile for the user and displays it.
        '''
        user = ctx.author

        if not user.id in self.bot.scoreboard.keys():
            await ctx.send(f'You have to play a game of trivia before a profile can be generated! Use `{self.bot.config["general"]["prefix"]} trivia` to take a quiz!')
            return

        embed = discord.Embed(title=f'{user.display_name}\'s profile')
        embed.set_thumbnail(url=user.avatar_url)
        embed.color = random.choice(self.bot.color_list)

        player_stats = self.get_scoreboard(user)

        embed.add_field(name=':abacus: Trivia games played:',
                        value=player_stats[0], inline=False)

        embed.add_field(name=':chart_with_upwards_trend: Percentage of games won:',
                        value=str(round((player_stats[1]/player_stats[0])*100, 1))+'%', inline=False)

        embed.add_field(name=':dart: Current streak:',
                        value=player_stats[2], inline=False)

        await ctx.send(embed=embed)

    @commands.command(name='trivia', aliases=['tr','triv','quiz'])
    async def trivia_quiz(self, ctx):
        '''
        a multiple-choice trivia quiz with ME-related questions
        '''
        player_stats = self.get_scoreboard(ctx.author)
        player_stats[0] += 1

        embed, question, correct_index, timeout = self.get_trivia_question(
            ctx.author, player_stats)
        await ctx.send(embed=embed, delete_after=timeout)

        if question in self.bot.stats_cache:
            qstats = list(self.bot.stats_cache[question])
            qstats[0] += 1
        else:
            qstats = [1, 0]

        # block user from sending any commands
        self.bot.blocked.append(ctx.author.id)
        try:
            # function to check whether the users's reply is valid
            def check(chk_msg):
                return chk_msg.author == ctx.author and chk_msg.channel == ctx.channel

            msg = await self.bot.wait_for('message', check=check, timeout=timeout)

            if not msg.content.isdecimal():  # not a digit
                await ctx.send(self.reply(False, ctx.author, '\nWhat is that supposed to be? Clearly not a digit...'))

            elif int(msg.content) == correct_index:  # right answer
                player_stats[1] += 1  # add one win
                player_stats[2] += 1  # add one to the streak
                qstats[1] += 1       # mark question as correctly answered
                if player_stats[2] and player_stats[2] % 5 == 0:
                    await ctx.send(self.reply(True, ctx.author, f'\n:dart: Streak of **{player_stats[2]} wins**! Keep it up!'))
                else:
                    await ctx.send(self.reply(True, ctx.author))

            else:  # invalid digit
                if player_stats[2] >= 5:
                    await ctx.send(self.reply(False, ctx.author, '\n:no_entry_sign: Your streak ended...'))
                else:
                    await ctx.send(self.reply(False, ctx.author))
                player_stats[2] = 0

        except asyncio.TimeoutError:
            await ctx.send(self.reply(False, ctx.author, '\nYou took too long to answer!'))

        # unblock user
        self.bot.blocked.remove(ctx.author.id)

        self.bot.stats_cache[question] = tuple(qstats)
        self.set_scoreboard(ctx.author, player_stats)

        # certain chance to send a small tip
        if random.random() <= self.bot.config['discord']['trivia']['tip_probability']:
            tip = random.choice(self.bot.config['discord']['trivia']['tips'])
            await ctx.send(tip.format(self.bot.config['discord']['trivia']['link']), delete_after=30)

    @commands.command(name='scoreboard')
    @commands.guild_only()
    async def display_scoreboard(self, ctx):
        '''
        display a trivia scoreboard for the server
        '''

        # fetching intersection of guild members and users on scoreboard
        found_users = [[user.name, *self.bot.scoreboard[user.id]] for user in ctx.guild.members if user.id in self.bot.scoreboard.keys() and self.bot.scoreboard[user.id][1] > 0]
        # sort users from best to worst
        found_users = sorted(found_users, key=lambda x: x[2])

        # prepare trivia embed
        scoreboard = ''
        medals = self.bot.config['discord']['trivia']['medals']
        scoreboard_line = self.bot.config['discord']['trivia']['scoreboard_line']

        count = 1
        for i, user in enumerate(found_users[::-1]):
            # create a formatted line for the user containing info about their games
            temp = scoreboard_line.format(user[2], round(user[2]/user[1]*100, 1), user[0])

            if user[3] >= 5:  # if user has an active streak, add a not to the line
                temp += self.bot.config['discord']['trivia']['scoreboard_streak'].format(user[3])

            # add a medal if necessary and append line to the scoreboard
            scoreboard += medals[min(i,len(medals)-1)].format(temp)+'\n'
            count += 1

            # break after X users (defined in config)
            if count >= self.bot.config['discord']['trivia']['scoreboard_max']:
                break

        # determine title, abort if fewer than two players have played a game yet
        if count > 1:
            title = f'Top {count} Trivia Players in *{ctx.guild}*'
        elif count == 1:
            await ctx.send(f'More than one person has to do a trivia quiz before a scoreboard can be generated. To see you own stats instead, use `{self.bot.config["general"]["prefix"]} profile`')
            return
        else:
            await ctx.send(f'You have to play a game of trivia before a scoreboard can be generated! Use `{self.bot.config["general"]["prefix"]} trivia` to take a quiz!')
            return

        #finish the scoreboard embed
        embed = discord.Embed(title=title, description=scoreboard,
                              color=random.choice(self.bot.color_list))

        # only create a graphical scoreboard if more than the defined minimum of players played a game yet
        if len(found_users) >= self.bot.config['discord']['trivia']['gscoreboard_min']:
            top_users = found_users[-1 * self.bot.config['discord']['trivia']['gscoreboard_max']:]
            len_users = len(top_users)
            names, g_taken, g_won, _ = list(zip(*top_users))
            index = np.arange(len_users)
            g_ratio = []
            max_val = max(g_won)+1

            for i in range(len_users):
                val = cogs._dcutils.map_vals(
                    g_won[i]/g_taken[i], .2, 1, 0, 1)
                g_ratio.append([1-val, val, 0])

            # create plot
            fig = plt.figure()

            # plot values
            plt.barh(index, g_won, color=g_ratio, label='Games won')

            # label axes, title plot
            plt.xlabel('Games won')
            plt.title('Trivia Scoreboard for {}'.format(ctx.guild.name))
            plt.yticks(index, names)
            plt.xticks(np.arange(max_val, step=round(
                math.ceil(max_val/5), -(int(math.log10(max_val)-1)))))

            # annotations & layout
            plt.annotate('Note: The greener the bar, the higher the winrate of the player.', (0, 0), (
                0, -40), xycoords='axes fraction', fontsize=8, textcoords='offset points', va='top')
            plt.tight_layout()

            # send plot
            with BytesIO() as buffer:
                fig.savefig(buffer, dpi=800)
                buffer.seek(0)
                await ctx.send(embed=embed, file=discord.File(fp=buffer, filename="scoreboard_{}.png".format(ctx.guild.id)))
                plt.close('all')
        else:
            await ctx.send(embed=embed)

    def get_scoreboard(self, user):
        if user.id in self.bot.scoreboard.keys():
            return list(self.bot.scoreboard[user.id])
        else:
            return [0, 0, 0]  # count, wins, streak

    def set_scoreboard(self, user, player_stats):
        self.bot.scoreboard[user.id] = tuple(player_stats)

    @commands.command(name='triviabattle', aliases=['tbattle', 'tb', 'trivia-battle', 'triviafight', 'tfight', 'tf'])
    @commands.guild_only()
    async def quote_battle(self, ctx):
        '''
        initiates and manages a trivia battle between two users
        '''

        # use the util to get a ready check from everyone involved
        result, players = await cogs._dcutils.handle_ready_check(self.bot, ctx)
        if not result:
            return

        # create user DMs, in case they did not yet exist
        scoreboard = {player:0 for player in players}
        max_char = 0
        for player in players:
            max_char = max(len(player.display_name),max_char)
            if not player.dm_channel:
                await player.create_dm()

        lead = [0, 0]
        # preparing score embed
        embed = discord.Embed(title='LotR Triviabattle', color=self.bot.config['discord']['colors']['DARK_RED'])
        embed.description = '```\n'
        for player, score in scoreboard.items():
            embed.description += f'{player.display_name.ljust(max_char+1)}: {score}\n'
        embed.description += '```'

        score_msg = await ctx.send(embed=embed)
        round_ind = 0
        timeout_rounds = 3

        def answer_check(chk_msg):
            # check whether author is opponent and channel is the corresponding DM
            if chk_msg.author in pending and chk_msg.channel == chk_msg.author.dm_channel:
                # remove user from pending
                pending.remove(chk_msg.author)
                if chk_msg.content.strip().isdecimal():
                    # save whether the answer is correct in answers
                    answers[player] = (int(chk_msg.content.strip()) == correct_index)
            # return true if pending is empty
            return not pending

        while True:
            # reset / manage round variables
            round_ind += 1
            pending = players.copy()
            answers = {player:-1 for player in players}

            # get new trivia question and distribute it
            embed, _, correct_index, timeout = self.get_trivia_question()
            for player in players:
                await player.dm_channel.send(embed=embed)

            # try to get an answer from all pending players
            try:
                await self.bot.wait_for('message', check=answer_check, timeout=timeout)
            except asyncio.TimeoutError:
                pass

            correct_answers = 0
            for player, won in answers:
                if won != -1:
                    correct_answers += won
                    scoreboard[player] += won
                    await player.dm_channel.send(self.reply(won, player))
                else:
                    await player.dm_channel.send(self.reply(False, player) + 'You didn\'t answer in time!')

            if correct_answers == 0:
                timeout_rounds -= 1
                if not timeout_rounds:
                    await ctx.send(self.bot.config['discord']['indicators'][0] + ' Game timed out.')
                    return
            else:
                timeout_rounds = 3
                for player in players:
                    await player.dm_channel.send(f'Round concluded. {correct_answers} out of {len(players)} players gave the right answer.')

            # determining leading two players
            lead = [0, 0]
            for score in scoreboard.values():
                if score > lead[0]:
                    lead.insert(0, score)
                elif score > lead[1]:
                    lead.insert(1, score)
                lead = lead[:2]

            # update score embed
            embed.description = '```\n'
            for player, score in scoreboard.items():
                embed.description += f'{player.display_name.ljust(max_char+1)}: {score}\n'
            embed.description += '```'
            if lead[0] > lead[1]:
                embed.set_footer('Matchpoint!')
            else:
                embed.set_footer('')
            await score_msg.edit(embed=embed)

            if lead[0] > lead[1]+1 > 1 and lead[0]+lead[1] > 2: #exit condition
                for player, score in scoreboard:
                    if score == lead[0]:
                        await ctx.send(f'Congratulations, {player.mention} You won the game!\n')
                        return
                await ctx.send(self.bot.config['discord']['indicators'][0] + ' Error while determining winner. Aborting.')


    def get_trivia_question(self, player=None, player_stats=None):
        correct_index = -1
        while correct_index < 0:
            # get random question
            with open('questions.csv', 'r') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                content = random.choice(list(csvreader))

            # pop the source and the question (first element)
            source = content.pop(0)
            question = content.pop(0)
            # shuffle answers
            random.shuffle(content)

            answers = content.copy()
            for i, item in enumerate(answers):
                if item.startswith(self.bot.config['discord']['trivia']['marker']):
                    answers[i] = item[1:]
                    correct_index = i+1
                    break
            if correct_index < 0:
                print('Invalid question found: {}'.format(question))

        embed = discord.Embed(title=question)
        if player_stats and player:
            embed.set_author(
                name=f'{player.display_name}\'s {cogs._dcutils.ordinal(player_stats[0])} trial in the Arts of Middle Earth trivia', url=player.avatar_url)
        else:
            embed.set_author(
                name='Your trial in the Arts of Middle Earth trivia')
        text = ''
        char_count = len(question)
        for num, answer in enumerate(answers):
            text += f'**{num+1}.)** {answer}\n'
            char_count += len(answer)
        embed.description = text

        # calculate the timeout
        timeout = round(char_count / self.bot.config['discord']['trivia']['multiplier'] +
                        self.bot.config['discord']['trivia']['extra_time'])

        embed.add_field(name=':stopwatch: Timeout:',
                        value=f'{timeout} seconds')
        embed.add_field(name=':book: Source:', value=source)
        embed.color = random.choice(self.bot.color_list)
        return (embed, question, correct_index, timeout)


def setup(bot):
    bot.add_cog(Trivia(bot))
