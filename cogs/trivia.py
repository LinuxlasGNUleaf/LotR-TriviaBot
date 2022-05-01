'''
Trivia cog for the LotR-Trivia Bot
'''
import asyncio
import csv
from io import BytesIO
import math
import logging
import random
from socket import timeout
import matplotlib.pyplot as plt
import numpy as np
import discord
from discord.ext import commands
from discord import ui
import backend_utils
import dc_utils

plt.rcdefaults()


class Trivia(commands.Cog):
    '''
    handles the LotR-Trivia integration for the bot, including profile / scoreboards
    '''

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)


    async def cog_load(self):
        self.logger.info('%s cog has been loaded.',
                         self.__class__.__name__.title())


    @dc_utils.category_check('minigames')
    @commands.command(name='profile')
    async def display_profile(self, ctx):
        '''
        displays the user's profile (concerning the trivia minigame)
        '''
        user = ctx.author
        if not user.id in self.bot.scoreboard.keys():
            await ctx.send(f'You have to play a game of trivia before a profile can be generated! Use `{self.bot.config["discord"]["prefix"]} trivia` to take a quiz!')
            return

        embed = discord.Embed(title=f'{user.display_name}\'s profile')
        embed.set_thumbnail(url=user.avatar.url)
        embed.color = random.choice(self.bot.color_list)

        player_stats = self.get_scoreboard(user)

        embed.add_field(name=':abacus: Trivia games played:',
                        value=player_stats[0], inline=False)

        embed.add_field(name=':chart_with_upwards_trend: Percentage of games won:',
                        value=str(round((player_stats[1]/player_stats[0])*100, 1))+'%', inline=False)

        embed.add_field(name=':dart: Current streak:',
                        value=player_stats[2], inline=False)

        await ctx.send(embed=embed)


    @dc_utils.category_check('minigames')
    @commands.command(name='trivia', aliases=['tr', 'triv', 'quiz'])
    async def trivia_quiz(self, ctx):
        '''
        a multiple-choice trivia quiz with ME-related questions
        '''
        view = TriviaView(ctx, self)


    @dc_utils.category_check('minigames')
    @commands.command(name='scoreboard')
    @commands.guild_only()
    async def display_scoreboard(self, ctx):
        '''
        displays a trivia scoreboard for the server
        '''
        # fetching intersection of guild members and users on scoreboard
        found_users = [[user.name, *self.bot.scoreboard[user.id]]
                       for user in ctx.guild.members if user.id in self.bot.scoreboard.keys() and self.bot.scoreboard[user.id][1] > 0]
        # sort users from best to worst
        found_users = sorted(found_users, key=lambda x: x[2])

        # prepare trivia embed
        scoreboard = ''
        medals = self.bot.config['trivia_quiz']['medals']
        scoreboard_line = self.bot.config['trivia_quiz']['scoreboard_line']

        count = 1
        for i, user in enumerate(found_users[::-1]):
            # create a formatted line for the user containing info about their games
            temp = scoreboard_line.format(user[2], round(user[2]/user[1]*100, 1), user[0])

            if user[3] >= 5:  # if user has an active streak, add a note to the line
                temp += self.bot.config['trivia_quiz']['scoreboard_streak'].format(user[3])

            # add a medal if necessary and append line to the scoreboard
            scoreboard += medals[min(i, len(medals)-1)].format(temp)+'\n'
            count += 1

            # break after X users (defined in config)
            if count > self.bot.config['trivia_quiz']['scoreboard_max']:
                break

        # determine title, abort if fewer than two players have played a game yet
        if count > 1:
            title = f'Top {count} Trivia Players in *{ctx.guild}*'
        elif count == 1:
            await ctx.send(f'More than one person has to do a trivia quiz before a scoreboard can be generated. To see you own stats instead, use `{self.bot.config["discord"]["prefix"]} profile`')
            return
        else:
            await ctx.send(f'You have to play a game of trivia before a scoreboard can be generated! Use `{self.bot.config["discord"]["prefix"]} trivia` to take a quiz!')
            return

        # finish the scoreboard embed
        embed = discord.Embed(title=title, description=scoreboard,
                              color=random.choice(self.bot.color_list))

        # only create a graphical scoreboard if more than the defined minimum of players played a game yet
        if len(found_users) >= self.bot.config['trivia_quiz']['gscoreboard_min']:
            top_users = found_users[-1 * self.bot.config['trivia_quiz']['gscoreboard_max']:]
            len_users = len(top_users)
            names, g_taken, g_won, _ = list(zip(*top_users))
            index = np.arange(len_users)
            g_ratio = []
            max_val = max(g_won)+1

            for i in range(len_users):
                val = dc_utils.map_vals(g_won[i]/g_taken[i], .2, 1, 0, 1)
                g_ratio.append([1-val, val, 0])

            # create plot
            fig = plt.figure()

            # plot values
            plt.barh(index, g_won, color=g_ratio, label='Games won')

            # label axes, title plot
            plt.xlabel('Games won')
            plt.title(f'Trivia Scoreboard for {ctx.guild.name}')
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
                await ctx.send(embed=embed, file=discord.File(fp=buffer, filename=f"scoreboard_{ctx.guild.id}.png"))
                plt.close('all')
        else:
            await ctx.send(embed=embed)


    def get_scoreboard(self, user):
        '''
        retrieves [count, wins, streak] for the userfrom the scoreboard
        '''
        return self.bot.caches['trivia_scores'].setdefault(user.id, [0,0,0])


    def set_scoreboard(self, user, count, wins, streak):
        '''
        writes [count, wins, streak] for the user to the scoreboard
        '''
        self.bot.caches['trivia_scores'][user.id] = [count, wins, streak]


    def get_trivia_question(self, player, count):
        '''
        retrieves question from .csv file
        '''
        correct_index = -1
        while correct_index < 0:
            # get random question
            with open('questions.csv', 'r', encoding='utf-8') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                content = random.choice(list(csvreader))

            # pop the source and the question (first element)
            source = content.pop(0)
            question = content.pop(0)
            # shuffle answers
            random.shuffle(content)

            answers = content.copy()
            for i, item in enumerate(answers):
                if item.startswith(self.bot.config['trivia_quiz']['marker']):
                    answers[i] = item[1:]
                    correct_index = i
                    break
            if correct_index < 0:
                print(f'Invalid question found: {question}')

        embed = discord.Embed(title=question)
        if player:
            embed.set_author(
                name=f'{player.display_name}\'s {backend_utils.ordinal(count)} trial in the Arts of Middle Earth trivia', url=player.avatar.url)
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
        timeout = round(char_count / self.bot.config['trivia_quiz']['multiplier'] +
                        self.bot.config['trivia_quiz']['extra_time'])

        embed.add_field(name=':stopwatch: Timeout:',
                        value=f'{timeout} seconds')
        embed.add_field(name=':book: Source:',
                        value=source)
        embed.color = self.bot.colors['AQUA']
        return (embed, len(answers), correct_index, timeout)

class TriviaQuizButton(discord.ui.Button['TriviaView']):
    def __init__(self, style: discord.ButtonStyle, i: int):
        self.index = i
        super().__init__(style=style, label=i+1)

    async def callback(self, _):
        await self.view.check_answer(self.index)

class TriviaSelectButton(discord.ui.Button['TriviaView']):
    def __init__(self, style: discord.ButtonStyle, i: int, correct: bool):
        self.index = i
        self.correct = correct
        super().__init__(style=style, label=i+1)

    async def callback(self, interaction: discord.Interaction):
        self.view.check_answer(self.index, self.correct)

class TriviaView(discord.ui.View):
    QUIZ = 1
    SELECT = 0
    WAIT = 2

    def __init__(self, context, cog):
        super().__init__()
        self.ctx = context
        self.bot = context.bot
        self.cog = cog

        self.trivia_msg = None

        self.trivia_buttons = []
        self.userstats = self.cog.get_scoreboard(self.ctx.author)
        self.correct_index = -1

        self.select_buttons = []

        self.setup_question()
    
    def setup_question(self):
        self.userstats[0] += 1
        # send trivia embed
        embed, answer_count, self.correct_index, timeout = self.cog.get_trivia_question(self.ctx.author, self.userstats[0])
        
        for i in range(answer_count):
            new_button = TriviaQuizButton(discord.ButtonStyle.blurple, i)
            self.add_item(new_button)
            self.trivia_buttons.append(new_button)
        self.game_state = self.QUIZ
        self.bot.loop.create_task(self.waitfor_response(embed, timeout))

    async def waitfor_response(self, embed, timeout):
        self.trivia_msg = await self.ctx.send(embed=embed, view=self)
        await asyncio.sleep(timeout)
        if self.game_state == self.QUIZ:
            await self.display_result(False)
    
    async def display_result(self, correct):
        await self.trivia_msg.edit(content=dc_utils.create_response(self.bot.config, self.ctx.author, correct),view=self)
        
    async def check_answer(self, button_index):
        if self.game_state == self.QUIZ:
            self.game_state == self.WAIT
        else:
            return
        correct = self.correct_index == button_index

        for i, button in enumerate(self.trivia_buttons):
            if i == button_index:
                button.style = discord.ButtonStyle.green if correct else discord.ButtonStyle.red
            button.disabled = True

        await self.display_result(correct)
        
async def setup(bot):
    await bot.add_cog(Trivia(bot))
