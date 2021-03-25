'''
Hangman cog for the LotR-Trivia Bot
'''
import csv
from random import shuffle, choice, random
import asyncio
import math
import matplotlib.pyplot as plt
from io import BytesIO
import numpy as np
import discord
from discord.ext import commands
import cogs._dcutils

plt.rcdefaults()

class Trivia(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.__class__.__name__} Cog has been loaded.')

    @commands.command(name='profile')
    async def display_profile(self, ctx):
        '''
        creates a profile for the ctx.author and displays it.
        '''
        if not ctx.author.id in self.bot.scoreboard.keys():
            await ctx.send('You have to play a game of trivia before a profile can be generated! Use `{} trivia` to take a quiz!'.format(self.bot.config['general']['key']))
            return

        player_stats = self.getScoreboard(ctx.author)
        win_ratio = player_stats[1]/player_stats[0]
        color = (cogs._dcutils.map_vals(win_ratio, 0, 1, 255, 0), cogs._dcutils.map_vals(win_ratio, 0, 1, 0, 255), 0)

        title = '{}\'s results'.format(ctx.author.display_name)
        content = 'Trivia games played: {}\nTrivia games won: {}\n\
                Win/Played ratio: {}%\n\
                Current Streak: {}'\
                .format(player_stats[0], player_stats[1], round(win_ratio*100, 2), player_stats[2])
        await ctx.send(embed=cogs._dcutils.create_embed(title, content=content, color=color))

    @commands.command(name='trivia')
    async def create_trivia_quiz(self, ctx):
        '''
        a multiple-choice trivia quiz with ME-related questions
        '''
        player_stats = self.getScoreboard(ctx.author)
        player_stats[0] += 1

        correct_index = -1
        while correct_index < 0:
            # get random question
            with open('questions.csv', 'r') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                content = choice(list(csvreader))

            # pop the source and the question (first element)
            source = content.pop(0)
            question = content.pop(0)
            # shuffle answers
            shuffle(content)

            answers = content.copy()
            for i, item in enumerate(answers):
                if item.startswith(self.bot.config['discord']['trivia']['marker']):
                    answers[i] = item[1:]
                    correct_index = i+1
                    if question in self.bot.stats_cache:
                        qstats = self.bot.stats_cache[question]
                        qstats[0] += 1
                    else:
                        qstats = (1, 0)
                    break
            if correct_index < 0:
                print('Invalid question found: {}'.format(question))

        # create author info
        author_name = '{}\'s {} trial in the Arts of Middle Earth trivia'\
            .format(ctx.author.display_name, cogs._dcutils.ordinal(player_stats[0]))
        author_info = (author_name, ctx.author.avatar_url)

        # create the embed text
        embed_text = '```markdown\n'
        char_count = len(question)
        for num, answer in enumerate(answers):
            embed_text += '{}. {}\n'.format(num+1, answer)
            char_count += len(answer)

        # calculate the timeout
        timeout = round(char_count / self.bot.config['discord']['trivia']['multiplier'] + \
                        self.bot.config['discord']['trivia']['extra_time'], 1)

        # add source and timeout to embed text
        embed_text += '```\nsource: {}'.format(source)
        embed_text += '\n:stopwatch: {} seconds'.format(round(timeout))

        await ctx.send(embed=cogs._dcutils.create_embed(question, author_info=author_info, content=embed_text), delete_after=timeout)

        # block user from sending any commands
        self.bot.blocked.append(ctx.author.id)
        try:
            # function to check whether the users's reply is valid
            def check(chk_msg):
                return chk_msg.author == ctx.author and chk_msg.channel == ctx.channel

            msg = await self.bot.bot.wait_for('message', check=check, timeout=timeout)

            if not msg.content.isdecimal(): # not a digit
                await self.trivia_reply(ctx, False, '\nWhat is that supposed to be? Clearly not a digit...')

            elif int(msg) == correct_index: # right answer
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

        self.bot.stats_cache[question] = qstats
        self.setScoreboard(ctx.author,player_stats)

        # certain chance to send a small tip
        if random() <= self.bot.config['discord']['trivia']['tip_probability']:
            tip = choice(self.bot.config['discord']['trivia']['tips'])
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
                found_users.append(user.name, *self.bot.scoreboard[user.id])
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
            title = 'Top {} Trivia Players in *{}*'.format(self.bot.config['discord']['trivia']['scoreboard_percent']*100, ctx.guild)
        elif count == 1:
            await ctx.send('More than one person has to do a trivia quiz before a scoreboard can be generated. To see you own stats instead, use `{} profile`'.format(self.bot.config['general']['key']))
        else:
            await ctx.send('You have to play a game of trivia before a scoreboard can be generated! Use `{} trivia` to take a quiz!'.format(self.bot.config['general']['key']))
            return

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
                await ctx.send(embed=cogs._dcutils.create_embed(title=title, content=scoreboard_string), file=discord.File(fp=buffer, filename="scoreboard_{}.png".format(ctx.guild.id)))
                plt.close('all')
        else:
            await ctx.send(embed=cogs._dcutils.create_embed(title=title, content=scoreboard_string))

    def getScoreboard(self, user):
        if user.id in self.bot.scoreboard.keys():
            return self.bot.scoreboard[user.id]
        else:
            return  (0, 0, 0) # count, wins, streak

    def setScoreboard(self, user, player_stats):
        self.bot.scoreboard[user.id] = player_stats

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
