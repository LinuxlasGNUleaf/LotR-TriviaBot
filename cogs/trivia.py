'''
Hangman cog for the LotR-Trivia Bot
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
    def __init__(self,bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)


    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.', self.__class__.__name__.title())

    @commands.command(name='profile')
    async def display_profile(self, ctx):
        '''
        creates a profile for the user and displays it.
        '''
        if not ctx.author.id in self.bot.scoreboard.keys():
            await ctx.send('You have to play a game of trivia before a profile can be generated! Use `{} trivia` to take a quiz!'.format(self.bot.config['general']['prefix']))
            return

        embed = discord.Embed(title=f'{ctx.author.display_name}\'s profile')
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.color = random.choice(self.bot.color_list)

        player_stats = self.get_scoreboard(ctx.author)

        win_ratio = player_stats[1]/player_stats[0]
        embed.add_field(name=':abacus: Trivia games played:',value=player_stats[0],inline=False)
        embed.add_field(name=':chart_with_upwards_trend: Percentage of games won:',value=str(round(win_ratio*100,1))+'%',inline=False)
        embed.add_field(name=':dart: Current streak:',value=player_stats[2],inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='trivia')
    async def create_trivia_quiz(self, ctx):
        '''
        a multiple-choice trivia quiz with ME-related questions
        '''
        player_stats = self.get_scoreboard(ctx.author)
        player_stats[0] += 1

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
        embed.set_author(name=f'{ctx.author.display_name}\'s {cogs._dcutils.ordinal(player_stats[0])} trial in the Arts of Middle Earth trivia',url=ctx.author.avatar_url)
        text = ''
        char_count = len(question)
        for num, answer in enumerate(answers):
            text += f'**{num+1}.)** {answer}\n'
            char_count += len(answer)
        embed.description = text

        # calculate the timeout
        timeout = round(char_count / self.bot.config['discord']['trivia']['multiplier'] + \
                        self.bot.config['discord']['trivia']['extra_time'])

        embed.add_field(name=':stopwatch: Timeout:',value=f'{timeout} seconds')
        embed.add_field(name=':book: Source:',value=source)
        embed.color = random.choice(self.bot.color_list)

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

            if not msg.content.isdecimal(): # not a digit
                await self.trivia_reply(ctx, False, '\nWhat is that supposed to be? Clearly not a digit...')

            elif int(msg.content) == correct_index: # right answer
                player_stats[1] += 1 # add one win
                player_stats[2] += 1 # add one to the streak
                qstats[1] += 1       # mark question as correctly answered
                if player_stats[2] and player_stats[2] % 5 == 0:
                    await self.trivia_reply(ctx, True, '\n:dart: Streak of **{player_stats[2]} wins**! Keep it up!')
                else:
                    await self.trivia_reply(ctx, True)

            else: # invalid digit
                if player_stats[2] >= 5:
                    await self.trivia_reply(ctx, False, '\n:no_entry_sign: Your streak ended...')
                else:
                    await self.trivia_reply(ctx, False)
                player_stats[2] = 0

        except asyncio.TimeoutError:
            await self.trivia_reply(ctx, False, '\nYou took too long to answer!')

        # unblock user
        self.bot.blocked.remove(ctx.author.id)

        self.bot.stats_cache[question] = tuple(qstats)
        self.set_scoreboard(ctx.author,player_stats)

        # certain chance to send a small tip
        if random.random() <= self.bot.config['discord']['trivia']['tip_probability']:
            tip = random.choice(self.bot.config['discord']['trivia']['tips'])
            await ctx.send(tip.format(self.bot.config['discord']['trivia']['link']), delete_after=30)


    @commands.command(name='scoreboard')
    async def display_scoreboard(self, ctx):
        '''
        display a trivia scoreboard for the server
        '''

        #finding trivia players and sorting them from highest to lowest
        found_users = []
        for user in ctx.guild.members:
            if user.id in self.bot.scoreboard.keys() and self.bot.scoreboard[user.id][1] > 0:
                found_users.append([user.name, *self.bot.scoreboard[user.id]])
        found_users = sorted(found_users, key=lambda x: x[2])

        #prepare trivia embed
        scoreboard_string = ''
        medals = ['🥇 **Eru Ilúvatar:**\n{}', '🥈 **Manwë:**\n{}', '🥉 Gandalf:\n{}\n', '👏 {}']
        user_str = '**[{} pts]** {} ({}%)'
        user_str2 = '**[{} pts]** {} ({}%) :dart: *Streak of {} wins*'
        count = 0
        for i, user in enumerate(found_users[::-1]):
            count += 1
            if user[3] >= 5: # if user has an active streak
                temp = user_str2.format(user[2], user[0], round(user[2]/user[1]*100, 1), user[3])
            else:
                temp = user_str.format(user[2], user[0], round(user[2]/user[1]*100, 1))

            if i < len(medals):
                scoreboard_string += medals[i].format(temp)+'\n'
            else:
                scoreboard_string += medals[-1].format(temp)+'\n'
            if count >= self.bot.config['discord']['trivia']['scoreboard_max']:
                break

        if count > 1:
            title = 'Top {} Trivia Players in *{}*'.format(self.bot.config['discord']['trivia']['scoreboard_max'], ctx.guild)
        elif count == 1:
            await ctx.send('More than one person has to do a trivia quiz before a scoreboard can be generated. To see you own stats instead, use `{} profile`'.format(self.bot.config['general']['prefix']))
            return
        else:
            await ctx.send('You have to play a game of trivia before a scoreboard can be generated! Use `{} trivia` to take a quiz!'.format(self.bot.config['general']['prefix']))
            return

        embed = discord.Embed(title=title, description=scoreboard_string, color=random.choice(self.bot.color_list))
        #prepare trivia scoreboard
        if len(found_users) >= self.bot.config['discord']['trivia']['graphical_scoreboard_min']:
            with BytesIO() as buffer:
                top_users = found_users[-15:]
                len_users = len(top_users)
                names, g_taken, g_won, _ = list(zip(*top_users))
                index = np.arange(len_users)
                g_ratio = []
                max_val = max(g_won)+1

                for i in range(len_users):
                    val = cogs._dcutils.map_vals(g_won[i]/g_taken[i], .2, 1, 0, 1)
                    g_ratio.append([1-val, val, 0])

                fig = plt.figure()
                # create plot
                plt.barh(index, g_won, color=g_ratio, label='Games won')
                plt.xlabel('Games won')
                plt.title('Trivia Scoreboard for {}'.format(ctx.guild.name))
                plt.yticks(index, names)
                plt.xticks(np.arange(max_val, step=round(math.ceil(max_val/5), -(int(math.log10(max_val)-1)))))
                plt.annotate('Note: The greener the bar, the higher the winrate of the player.', (0, 0), (0, -40), xycoords='axes fraction', fontsize=8, textcoords='offset points', va='top')
                plt.tight_layout()

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
            return  [0, 0, 0] # count, wins, streak

    def set_scoreboard(self, user, player_stats):
        self.bot.scoreboard[user.id] = tuple(player_stats)

    async def trivia_reply(self,ctx, won, text=''):
        '''
        creates a reply to an user, insult or compliment
        '''
        if won:
            msg = ':white_check_mark: ' + random.choice(self.bot.config['discord']['compliments'])
        else:
            msg = ':x: ' + random.choice(self.bot.config['discord']['insults'])
        await ctx.send(msg if '{}' not in msg else msg.format(ctx.author.display_name)+text)


def setup(bot):
    bot.add_cog(Trivia(bot))
