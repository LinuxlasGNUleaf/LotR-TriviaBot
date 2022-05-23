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

import backend_utils
import dc_utils

plt.rcdefaults()


class Trivia(commands.Cog):
    """
    handles the LotR-Trivia integration for the bot, including profile / scoreboards
    """

    def __init__(self, bot):
        self.bot = bot
        self.options = self.bot.config['trivia_quiz']
        self.questions_location = self.bot.config['backend']['assets']['questions']
        self.logger = logging.getLogger(__name__)

    async def cog_load(self):
        self.logger.info('%s cog has been loaded.',
                         self.__class__.__name__.title())

    @dc_utils.category_check('minigames')
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

        embed = discord.Embed(title=f'{user.display_name}\'s profile')
        embed.set_thumbnail(url=user.avatar.url)
        embed.colour = random.choice(self.bot.color_list)

        player_stats = self.get_scoreboard(user)

        embed.add_field(name=':abacus: Trivia games played:',
                        value=player_stats[0], inline=False)

        embed.add_field(name=':chart_with_upwards_trend: Percentage of games won:',
                        value=str(round((player_stats[1] / player_stats[0]) * 100, 1)) + '%', inline=False)

        embed.add_field(name=':dart: Current streak:',
                        value=player_stats[2], inline=False)

        await ctx.send(embed=embed)

    @dc_utils.category_check('minigames')
    @commands.command(name='trivia', aliases=['tr', 'quiz'])
    async def trivia_quiz(self, ctx):
        """
        a multiple-choice trivia quiz with ME-related questions
        """
        TriviaGameUI(ctx, self)

    @dc_utils.category_check('minigames')
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
        medals = self.options['scoreboard_medals']
        scoreboard_line = self.options['scoreboard_entry']

        count = 1
        for i, user in enumerate(found_users[::-1]):
            # create a formatted line for the user containing info about their games
            temp = scoreboard_line.format(user[2], round(user[2] / user[1] * 100, 1), user[0])

            if user[3] >= 5:  # if user has an active streak, add a note to the line
                temp += self.options['scoreboard_streak_info'].format(user[3])

            # add a medal if necessary and append line to the scoreboard
            scoreboard += medals[min(i, len(medals) - 1)].format(temp) + '\n'
            count += 1

            # break after X users (defined in config)
            if count > self.options['scoreboard_length']:
                break

        # determine title, abort if fewer than two players have played a game yet
        if count > 1:
            title = f'Top {count} Trivia Players in *{ctx.guild}*'
        elif count == 1:
            await ctx.send(
                f'More than one person has to do a trivia quiz before a scoreboard can be generated. To see you own stats instead, use the `profile` command.')
            return
        else:
            await ctx.send(
                f'You have to play a game of trivia before a scoreboard can be generated! Use the `trivia` command to take a quiz!')
            return

        # finish the scoreboard embed
        embed = discord.Embed(title=title, description=scoreboard,
                              color=random.choice(self.bot.color_list))

        # only create a graphical scoreboard if more than the defined minimum of players played a game yet
        if len(found_users) >= self.options['gscoreboard_min']:
            top_users = found_users[-1 * self.options['gscoreboard_length']:]
            len_users = len(top_users)
            names, g_taken, g_won, _ = list(zip(*top_users))
            index = np.arange(len_users)
            g_ratio = []
            max_val = max(g_won) + 1

            for i in range(len_users):
                val = backend_utils.map_vals(g_won[i] / g_taken[i], .2, 1, 0, 1)
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

    def get_trivia_question(self, player, count):
        """
        retrieves question from .csv file
        """
        # get random question
        with open(self.questions_location, 'r', encoding='utf-8') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            content = random.choice(list(csvreader))

        # pop the source and the question (first element)
        source = content.pop(0)
        question = content.pop(0)
        # shuffle answers
        random.shuffle(content)

        answers = content.copy()
        correct_index = -1
        for i, item in enumerate(answers):
            if item.startswith(self.options['question_marker']):
                answers[i] = item[1:]
                correct_index = i
                break

        embed = discord.Embed(title=question)
        if player:
            embed.set_author(
                name=f'{player.display_name}\'s {backend_utils.ordinal(count)} trial in the Arts of Middle Earth trivia',
                url=player.avatar.url)
        else:
            embed.set_author(
                name='Your trial in the Arts of Middle Earth trivia')
        text = ''
        char_count = len(question)
        for num, answer in enumerate(answers):
            text += f'**{num + 1}.)** {answer}\n'
            char_count += len(answer)
        embed.description = text

        # calculate the timeout
        timeout = round(char_count / self.options['chars_per_seconds'] +
                        self.options['min_read_time'])

        embed.add_field(name=':stopwatch: Timeout:',
                        value=f'{timeout} seconds')
        embed.add_field(name=':book: Source:',
                        value=source)
        embed.add_field(name=':newspaper: Results of the last battle:',
                        value='```\n ```',
                        inline=False)
        embed.colour = self.bot.colors['AQUA']
        return embed, len(answers), correct_index, timeout


class TriviaQuizButton(discord.ui.Button['TriviaView']):
    def __init__(self, style: discord.ButtonStyle, i: int, correct: bool):
        self.index = i
        self.correct = correct
        super().__init__(style=style, label=str(i + 1))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.style = discord.ButtonStyle.green if self.correct else discord.ButtonStyle.red
        await self.view.finish_quiz(self.correct)


class TriviaSelectButton(discord.ui.Button['TriviaView']):
    def __init__(self, style: discord.ButtonStyle, title: str, continue_game: bool):
        self.continue_game = continue_game
        super().__init__(style=style, label=title, row=2)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.continue_game:
            self.view.delete_all_buttons()
            self.view.setup_quiz()
        else:
            self.view.delete_all_buttons()
            await self.view.update_message()
            self.view.stop()


class TriviaGameUI(discord.ui.View):

    def __init__(self, context, cog):
        super().__init__()
        self.ctx = context
        self.bot = context.bot
        self.cog = cog

        self.trivia_msg = None
        self.trivia_embed = None
        self.trivia_note = None
        self.trivia_hint = None

        self.quiz_running = False
        self.quiz_counter = 0

        self.buttons = []
        self.user_stats = self.cog.get_scoreboard(self.ctx.author)
        self.correct_index = -1

        self.setup_quiz()

    def disable_all_buttons(self):
        for i, button in enumerate(self.buttons):
            button.disabled = True

    def delete_all_buttons(self):
        self.clear_items()
        self.buttons.clear()

    async def update_message(self):
        self.trivia_embed.set_field_at(len(self.trivia_embed.fields) - 1,
                                       name=self.trivia_embed.fields[-1].name,
                                       value=f'```\n{self.trivia_note if self.trivia_note else " "}```',
                                       inline=False)
        if self.trivia_hint:
            self.trivia_embed.set_footer(text=self.trivia_hint)
        else:
            self.trivia_embed.remove_footer()

        if self.trivia_msg:
            await self.trivia_msg.edit(embed=self.trivia_embed, view=self)
        else:
            self.trivia_msg = await self.ctx.send(embed=self.trivia_embed, view=self)

    async def on_timeout(self):
        self.disable_all_buttons()
        await self.update_message()

    def setup_quiz(self):
        self.user_stats[0] += 1
        self.quiz_counter += 1
        # send trivia embed
        self.trivia_embed, answer_count, self.correct_index, timeout = self.cog.get_trivia_question(self.ctx.author,
                                                                                                    self.user_stats[0])

        # setup trivia question buttons
        self.delete_all_buttons()
        for i in range(answer_count):
            new_button = TriviaQuizButton(discord.ButtonStyle.blurple, i, i == self.correct_index)
            self.add_item(new_button)
            self.buttons.append(new_button)

        # run quiz
        self.bot.loop.create_task(self.run_quiz(timeout))

    async def run_quiz(self, timeout):
        self.quiz_running = True
        self.timeout = None
        current_quiz = self.quiz_counter
        await self.update_message()
        await asyncio.sleep(timeout)
        if self.quiz_running and current_quiz == self.quiz_counter:
            await self.finish_quiz(False, timeout=True)

    async def finish_quiz(self, correct, timeout=False):
        if not self.quiz_running:
            return
        self.quiz_running = False

        # adjust win count of player accordingly
        self.user_stats[1] += correct

        self.trivia_note = dc_utils.create_response(self.bot.config, self.ctx.author, correct)
        if timeout:
            self.trivia_hint = "\nYou didn't answer in time!"
        elif random.uniform(0, 1) <= self.cog.options['tip_probability']:
            self.trivia_hint = random.choice(self.cog.options['tips']).format(self.cog.options['link'])
        else:
            self.trivia_hint = None

        continue_button = TriviaSelectButton(discord.ButtonStyle.green, 'CONTINUE', True)
        stop_button = TriviaSelectButton(discord.ButtonStyle.red, 'STOP', False)

        # disable all quiz buttons
        self.disable_all_buttons()

        # add select buttons
        self.add_item(continue_button)
        self.add_item(stop_button)
        self.buttons.append(continue_button)
        self.buttons.append(stop_button)

        self.timeout = self.cog.options['select_timeout']
        await self.update_message()


async def setup(bot):
    await bot.add_cog(Trivia(bot))
