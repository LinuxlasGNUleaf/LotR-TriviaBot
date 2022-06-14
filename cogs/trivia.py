"""
Trivia cog for the LotR-Trivia Bot
"""
import asyncio
import csv
import math
import random
from io import BytesIO

import discord
import matplotlib.pyplot as plt
import numpy as np
from discord.ext import commands

import backend_utils as bu
import discord_utils as du
from template_cog import LotrCog

plt.rcdefaults()


class Trivia(LotrCog):
    """
    handles the LotR-Trivia-Quiz integration for the bot, including profile / scoreboards
    """

    def __init__(self, bot):
        super().__init__(bot)

    async def cog_load(self):
        self.logger.info('%s cog has been loaded.',
                         self.__class__.__name__.title())

    @du.category_check('minigames')
    @commands.command(name='profile', aliases=['tp', 'tstat'])
    async def display_profile(self, ctx):
        """
        displays the user's profile (concerning the trivia minigame)
        """
        user = ctx.author
        if user.id not in self.caches['scores']:
            await ctx.send(
                f'You have to play a game of trivia before a profile can be generated! Use the `trivia` command to take a quiz!')
            return

        embed = discord.Embed(title=f'{user.display_name}\'s profile')
        embed.set_thumbnail(url=user.avatar.url)
        embed.colour = discord.Color.random()

        player_stats = self.get_scoreboard(user)

        embed.add_field(name=':abacus: Trivia games played:',
                        value=player_stats[0], inline=False)

        embed.add_field(name=':chart_with_upwards_trend: Percentage of games won:',
                        value=str(round((player_stats[1] / player_stats[0]) * 100, 1)) + '%', inline=False)

        embed.add_field(name=':dart: Current streak:',
                        value=player_stats[2], inline=False)

        await ctx.send(embed=embed)

    @du.category_check('minigames')
    @commands.command(name='trivia', aliases=['tr', 'quiz'])
    async def trivia_quiz(self, ctx):
        """
        a multiple-choice trivia quiz with ME-related questions
        """
        TriviaGameUI(ctx, self)

    @du.category_check('minigames')
    @commands.command(name='scoreboard')
    @commands.guild_only()
    async def display_scoreboard(self, ctx):
        """
        displays a trivia scoreboard for the server
        """
        # fetching intersection of guild members and users on scoreboard
        found_users = [[user.name, *self.caches['scores'][user.id]]
                       for user in ctx.guild.members if
                       user.id in self.caches['scores'].keys() and self.caches['scores'][user.id][1] > 0]
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
                              color=discord.Color.random())

        # only create a graphical scoreboard if more than the defined minimum of players played a game yet
        if len(found_users) >= self.options['gscoreboard_min']:
            top_users = found_users[-1 * self.options['gscoreboard_length']:]
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
        return list(self.caches['scores'].setdefault(user.id, [0, 0, 0]))

    def set_scoreboard(self, user, count, wins, streak):
        """
        writes [count, wins, streak] for the user to the scoreboard
        """
        self.caches['scores'][user.id] = [count, wins, streak]

    def get_trivia_question(self, player, count):
        """
        retrieves question from .csv file
        """
        # get random question
        with open(self.assets['questions'], 'r', encoding='utf-8') as csvfile:
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

        text = ''
        char_count = len(question)
        for num, answer in enumerate(answers):
            text += f'**{num + 1}.)** {answer}\n'
            char_count += len(answer)

        author_field = (
            f'{player.display_name}\'s {bu.ordinal(count)} trial in the Arts of Middle Earth trivia' if player
            else 'Your trial in the Arts of Middle Earth trivia',
            None,
            (player.avatar if player.avatar else player.default_avatar).url
        )

        embed = du.create_embed(title=question, author_field=author_field, content=text, color=discord.Color.teal())

        # calculate the timeout
        timeout = round(char_count / self.options['chars_per_seconds'] +
                        self.options['min_read_time'])

        embed.add_field(name=':stopwatch: Timeout:',
                        value=f'{timeout} seconds')
        embed.add_field(name=':book: Source:',
                        value=source)
        embed.add_field(name=':newspaper: Results of the last quiz:',
                        value='```\n ```',
                        inline=False)
        return embed, len(answers), correct_index, timeout

    def create_response(self, user, positive):
        msg = random.choice(self.options['compliments'] if positive else self.options['insults'])
        return msg.format(user.display_name)


class TriviaQuizButton(discord.ui.Button['TriviaView']):
    def __init__(self, style: discord.ButtonStyle, i: int, correct: bool):
        self.index = i
        self.correct = correct
        super().__init__(style=style, label=str(i + 1))

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.view.ctx.author.id:
            await interaction.response.defer()
            self.style = discord.ButtonStyle.green if self.correct else discord.ButtonStyle.red
            await self.view.finish_quiz(self.correct)
        elif interaction.user.id not in self.view.warned_users:
            self.view.warned_users.append(interaction.user.id)
            await interaction.response.send_message("You are not the user that started this quiz!", ephemeral=True)
        else:
            await interaction.response.defer()


class TriviaSelectButton(discord.ui.Button['TriviaView']):
    def __init__(self, style: discord.ButtonStyle, title: str, continue_game: bool):
        self.continue_game = continue_game
        super().__init__(style=style, label=title, row=2)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.view.ctx.author.id:
            await interaction.response.defer()
            if self.continue_game:
                self.view.delete_all_buttons()
                self.view.setup_quiz()
            else:
                self.view.delete_all_buttons()
                await self.view.update_message()
                self.view.stop()
        elif interaction.user.id not in self.view.warned_users:
            self.view.warned_users.append(interaction.user.id)
            await interaction.response.send_message("You are not the user that started this quiz!", ephemeral=True)
        else:
            await interaction.response.defer()


class TriviaGameUI(discord.ui.View):

    def __init__(self, context, cog):
        super().__init__()
        self.ctx = context
        self.user = context.author
        self.bot = context.bot
        self.cog = cog

        self.trivia_msg = None
        self.trivia_embed = None
        self.trivia_note = None
        self.trivia_hint = None

        self.quiz_running = False
        self.quiz_counter = 0

        self.buttons = []
        self.warned_users = []
        self.user_stats = self.cog.get_scoreboard(self.user)
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
        self.cog.set_scoreboard(self.user, *self.user_stats)
        self.quiz_counter += 1
        # send trivia embed
        self.trivia_embed, answer_count, self.correct_index, timeout = self.cog.get_trivia_question(self.user,
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
        self.cog.set_scoreboard(self.user, *self.user_stats)

        self.trivia_note = self.cog.create_response(self.ctx.author, correct)
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
