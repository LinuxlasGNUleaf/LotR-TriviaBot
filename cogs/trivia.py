"""
Trivia cog for the LotR-Trivia Bot
"""
import asyncio
import csv
import logging
import math
import random
from io import BytesIO

import discord
import matplotlib.pyplot as plt
import numpy as np
from discord.ext import commands

import backend_utils as bu
import dc_utils as du

plt.rcdefaults()


class Trivia(commands.Cog):
    """
    handles the LotR-Trivia integration for the bot, including profile / scoreboards
    """

    def __init__(self, bot):
        self.bot = bot
        self.options = self.bot.config['trivia_quiz']
        self.logger = logging.getLogger(__name__)

        # parse questions
        self.questions = []
        with open(self.bot.get_asset_name('questions'), 'r', encoding='utf-8') as csv_file:
            for line in csv.reader(csv_file, delimiter=',', quotechar='"'):
                source, question, *answers = line
                for answer_i, answer in enumerate(answers):
                    if answer.startswith(self.options['marker']):
                        correct_index = answer_i
                        answers[answer_i] = answer[1:]
                        break
                else:
                    continue
                self.questions.append([source, question, correct_index, *answers])

    async def cog_load(self):
        self.logger.info('%s cog has been loaded.',
                         self.__class__.__name__.title())

    @du.category_check('minigames')
    @commands.command(name='profile')
    async def display_profile(self, ctx):
        """
        displays the user's profile (concerning the trivia minigame)
        """
        user = ctx.author
        if user.id not in self.bot.scoreboard.keys():
            await ctx.send(
                f'You have to play a game of trivia before a profile can be generated! Use `{self.bot.config["discord"]["prefix"]} trivia` to take a quiz!')
            return

        embed = discord.Embed(title=f'{user.display_name}\'s profile', color=random.choice(self.bot.color_list))
        embed.set_thumbnail(url=user.avatar.url)

        player_stats = self.get_scoreboard(user)

        embed.add_field(name=':abacus: Trivia games played:',
                        value=player_stats[0], inline=False)

        embed.add_field(name=':chart_with_upwards_trend: Percentage of games won:',
                        value=str(round((player_stats[1] / player_stats[0]) * 100, 1)) + '%', inline=False)

        embed.add_field(name=':dart: Current streak:',
                        value=player_stats[2], inline=False)

        await ctx.send(embed=embed)

    @du.category_check('minigames')
    @commands.command(name='trivia', aliases=['tr', 'triv', 'quiz'])
    async def trivia_quiz(self, ctx):
        """
        a multiple-choice trivia quiz with ME-related questions
        """
        view = TriviaGameUI(ctx, self)

    @du.category_check('minigames')
    @commands.command(name='scoreboard')
    @commands.guild_only()
    async def display_scoreboard(self, ctx):
        """
        displays a trivia scoreboard for the server
        """
        # fetching intersection of guild members and users on scoreboard
        found_users = [[user.name, *self.bot.scoreboard[user.id]]
                       for user in ctx.guild.members if
                       user.id in self.bot.scoreboard.keys() and self.bot.scoreboard[user.id][1] > 0]
        # sort users from best to worst
        found_users = sorted(found_users, key=lambda x: x[2])

        # prepare trivia embed
        scoreboard = ''
        medals = self.options['medals']
        scoreboard_line = self.options['scoreboard_line']

        count = 1
        for i, user in enumerate(found_users[::-1]):
            # create a formatted line for the user containing info about their games
            temp = scoreboard_line.format(user[2], round(user[2] / user[1] * 100, 1), user[0])

            if user[3] >= 5:  # if user has an active streak, add a note to the line
                temp += self.options['scoreboard_streak'].format(user[3])

            # add a medal if necessary and append line to the scoreboard
            scoreboard += medals[min(i, len(medals) - 1)].format(temp) + '\n'
            count += 1

            # break after X users (defined in config)
            if count > self.options['scoreboard_max']:
                break

        # determine title, abort if fewer than two players have played a game yet
        if count > 1:
            title = f'Top {count} Trivia Players in *{ctx.guild}*'
        elif count == 1:
            await ctx.send(
                f'More than one person has to do a trivia quiz before a scoreboard can be generated. To see you own stats instead, use `{self.bot.config["discord"]["prefix"]} profile`')
            return
        else:
            await ctx.send(
                f'You have to play a game of trivia before a scoreboard can be generated! Use `{self.bot.config["discord"]["prefix"]} trivia` to take a quiz!')
            return

        # finish the scoreboard embed
        embed = discord.Embed(title=title, description=scoreboard,
                              color=random.choice(self.bot.color_list))

        # only create a graphical scoreboard if more than the defined minimum of players played a game yet
        if len(found_users) >= self.options['gscoreboard_min']:
            top_users = found_users[-1 * self.options['gscoreboard_max']:]
            len_users = len(top_users)
            names, g_taken, g_won, _ = list(zip(*top_users))
            index = np.arange(len_users)
            g_ratio = []
            max_val = max(g_won) + 1

            for i in range(len_users):
                val = bu.map_values(g_won[i] / g_taken[i], .2, 1, 0, 1)
                g_ratio.append([1 - val, val, 0])

            # create plot
            fig = plt.figure()

            # plot values
            plt.barh(index, g_won, color=g_ratio, label='Games won')

            # label axes, title plot
            plt.xlabel('Games won')
            plt.title(f'Trivia Scoreboard for {ctx.guild.name}')
            plt.yticks(index, names)
            plt.xticks(np.arange(max_val, step=round(
                math.ceil(max_val / 5), -(int(math.log10(max_val) - 1)))))

            # annotations & layout
            plt.annotate('Note: The greener the bar, the higher the win rate of the player.', (0, 0), (
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
        """
        retrieves [count, wins, streak] for the user from the scoreboard
        """
        return self.bot.caches['trivia_scores'].setdefault(user.id, [0, 0, 0])

    def set_scoreboard(self, user, count, wins, streak):
        """
        writes [count, wins, streak] for the user to the scoreboard
        """
        self.bot.caches['trivia_scores'][user.id] = [count, wins, streak]


class TriviaQuizButton(discord.ui.Button['TriviaView']):
    def __init__(self, style: discord.ButtonStyle, i: int):
        self.index = i
        super().__init__(style=style, label=str(i + 1))

    async def callback(self, _):
        await self.view.check_answer(self.index)


class TriviaSelectButton(discord.ui.Button['TriviaView']):
    def __init__(self, style: discord.ButtonStyle, i: int, correct: bool):
        self.index = i
        self.correct = correct
        super().__init__(style=style, label=str(i + 1))

    async def callback(self, interaction: discord.Interaction):
        self.view.check_answer(self.index, self.correct)


class TriviaGameUI(discord.ui.View):
    SELECT = 0
    QUIZ = 1
    WAIT = 2

    def __init__(self, context, cog):
        super().__init__()
        self.ctx = context
        self.bot = context.bot
        self.cog = cog

        self.trivia_msg = None

        self.buttons = []
        self.user = self.ctx.author
        self.user_stats = self.cog.get_scoreboard(self.user)
        self.correct_index = -1
        self.game_state = self.SELECT

        self.setup_question()

    def setup_question(self):
        self.user_stats[0] += 1

        source, question, correct_index, *answers = random.choice(self.cog.questions)

        # send trivia embed
        embed = discord.Embed(title=question, color=self.bot.colors['AQUA'])
        embed.set_author(
            name=f'{self.user.display_name}\'s {bu.ordinal(self.user_stats[0])} trial in the Arts of Middle Earth trivia',
            url=self.user.avatar.url)
        embed.description = '\n'.join([f'**{num + 1}.)** {answer}' for num, answer in enumerate(answers)])

        # calculate the timeout
        char_count = len(question) + sum([len(answer) for answer in answers])
        timeout = round(char_count / self.cog.options['multiplier'] +
                        self.cog.options['extra_time'])

        # add info
        embed.add_field(name=':stopwatch: Timeout:',
                        value=f'{timeout} seconds')
        embed.add_field(name=':book: Source:',
                        value=source)

        for i in range(len(answers)):
            new_button = TriviaQuizButton(discord.ButtonStyle.blurple, i)
            self.add_item(new_button)
            self.buttons.append(new_button)
        self.game_state = self.QUIZ
        self.bot.loop.create_task(self.run_quiz(embed, timeout))

    async def run_quiz(self, embed, timeout):
        self.trivia_msg = await self.ctx.send(embed=embed, view=self)
        await asyncio.sleep(timeout)
        if self.game_state == self.QUIZ:
            await self.display_result(False)

    async def display_result(self, correct):
        await self.trivia_msg.edit(content=du.create_response(self.bot.config, self.ctx.author, correct),
                                   view=self)

    async def check_answer(self, button_index):
        if self.game_state == self.QUIZ:
            self.game_state = self.WAIT
        else:
            return

        # determine whether player won, and adjust win count accordingly
        correct = self.correct_index == button_index
        self.user_stats[1] += correct

        # disable all buttons and highlight the selected button in the right color
        for i, button in enumerate(self.buttons):
            if i == button_index:
                button.style = discord.ButtonStyle.green if correct else discord.ButtonStyle.red
            button.disabled = True

        await self.display_result(correct)


async def setup(bot):
    await bot.add_cog(Trivia(bot))
