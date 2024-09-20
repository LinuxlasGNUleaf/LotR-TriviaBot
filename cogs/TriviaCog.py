import csv
import math
import random
import typing
import warnings
import io

import discord
import numpy as np
from discord import app_commands
from matplotlib import pyplot as plt

from src import utils, DataManager
from src.DefaultCog import DefaultCog
from src.CustomUIs import TriviaView


class TriviaCog(DefaultCog, group_name='trivia'):
    """
    lotr-themed trivia quiz, profile and scoreboard functions
    """

    @app_commands.command(name='play')
    async def trivia(self, interaction: discord.Interaction):
        """
        a multiple-choice trivia quiz with ME-related questions
        """
        TriviaView(interaction, self)

    @app_commands.command(name='profile')
    @app_commands.describe(member='The user you want to fetch the profile of')
    async def display_profile(self, interaction: discord.Interaction, member: typing.Optional[discord.Member]):
        """
        displays the user's profile (concerning the trivia minigame)
        """
        member = member if member is not None else interaction.user
        if member.id not in self.data['scores']:
            await interaction.response.send_message(
                f"{member.mention} hasn't played a game of trivia yet. To play, use the `/trivia` command!",
                ephemeral=True)
            return
        embed = discord.Embed(title=f'{utils.genitive(member.display_name)} profile')
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar)
        embed.colour = discord.Color.random()

        count, points, streak = self.data['scores'].get_row(member.id)

        embed.add_field(name=':chart_with_upwards_trend: Points earned:',
                        value=points,
                        inline=False)
        embed.add_field(name=':abacus: Trivia games played:',
                        value=count,
                        inline=False)
        embed.add_field(name=':dart: Current streak:',
                        value=streak,
                        inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='scoreboard')
    @app_commands.guild_only()
    async def display_scoreboard(self, interaction: discord.Interaction):
        """
        displays a trivia scoreboard for the server
        """
        # fetching all player ids from DB
        player_ids = self.data['scores'].keys()
        players = []

        for member in interaction.guild.members:
            # if member hasn't played yet
            if member.id not in player_ids:
                continue
            temp_entry = [member.mention, *self.data['scores'].get(member.id, ['played', 'points', 'streak'])]
            # if member hasn't won a game yet
            if temp_entry[2] == 0:
                continue
            players.append(temp_entry)

        # sort players from best to worst
        players.sort(key=lambda x: x[2])

        # prepare trivia embed
        scoreboard = ''

        rank = 0
        for name, count, points, streak in players[::-1]:
            # create a formatted line for the player containing info about their games

            if streak < self.config['scoreboard']['min_streak']:
                temp = (self.config['scoreboard']['default_template']
                        .format(score=str(points).rjust(5, ' '),
                                name=name))
            # if player has an active streak, note it on the scoreboard
            else:
                temp = (self.config['scoreboard']['streak_template']
                        .format(score=str(points).rjust(5, ' '),
                                name=name,
                                streak=streak))
            rank += 1
            scoreboard += f'{temp}\n'
            if rank > 1 and rank % 5 == 1:
                scoreboard += '\n'
            # break after X users (defined in config)
            if rank > self.config['scoreboard']['length']:
                break

        # determine title, abort if fewer than two players have played a game yet
        if rank > 1:
            title = f'Top {rank} Trivia Players in *`{interaction.guild}`*'
        elif rank == 1:
            await interaction.response.send_message(
                f'More than one person has to do a trivia quiz before a scoreboard can be generated. To see you own stats instead, use the `profile` command.')
            return
        else:
            await interaction.response.send_message(
                f'You have to play a game of trivia before a scoreboard can be generated! Use the `trivia` command to take a quiz!')
            return

        # finish the scoreboard embed
        embed = discord.Embed(title=title, description=scoreboard, color=discord.Color.random())

        # only create a graphical scoreboard if more than the defined minimum of players played a game yet
        if len(players) >= self.config['scoreplot']['players_range'][0]:
            top_users = players[-1 * self.config['scoreplot']['players_range'][1]:]
            len_users = len(top_users)
            names, g_taken, g_won, _ = list(zip(*top_users))
            index = np.arange(len_users)
            g_ratio = []
            max_val = max(g_won) + 1

            for i in range(len_users):
                val = utils.map_values(g_won[i] / g_taken[i], .2, 1, 0, 1)
                g_ratio.append([1 - val, val, 0])

            # create plot
            fig = plt.figure()

            # plot values
            plt.barh(index, g_won, color=g_ratio, label='Games won')

            # label axes, title plot
            plt.xlabel('Games won')
            plt.title(f'Trivia Scoreboard for {interaction.guild.name}')
            plt.yticks(index, names)
            plt.xticks(np.arange(max_val, step=round(
                math.ceil(max_val / 5), -(int(math.log10(max_val) - 1)))))

            # annotations & layout
            plt.annotate('Note: The greener the bar, the higher the win rate of the player.', (0, 0), (
                0, -40), xycoords='axes fraction', fontsize=8, textcoords='offset points', va='top')
            plt.tight_layout()

            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=UserWarning)
                # send plot
                with io.BytesIO() as buffer:
                    fig.savefig(buffer, dpi=800)
                    buffer.seek(0)
                    await interaction.response.send_message(embed=embed, file=discord.File(fp=buffer, filename=f"scoreboard_{interaction.guild.id}.png"))
                    plt.close('all')
        else:
            await interaction.response.send_message(embed=embed)

    def get_trivia_question(self, player, count):
        """
        retrieves question from .csv file
        """
        # get random question
        with open(self.assets['questions'], 'r', encoding='utf-8') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            content = random.choice(list(csvreader))

        # extract info from line
        source, level, question, *answers = content
        # TODO: use the level info

        # new convention dictates that the first answer specified is the correct one
        correct_answer = answers[0]

        # shuffle answers
        random.shuffle(answers)
        correct_index = answers.index(correct_answer)

        text = ''
        char_count = len(question) + sum(len(answer) for answer in answers)
        for num, answer in enumerate(answers):
            text += f'**{num + 1}.)** {answer}\n'

        author_field = (
            f'{player.display_name}\'s {utils.ordinal(count)} trial in the Arts of Middle Earth trivia' if player
            else 'Your trial in the Arts of Middle Earth trivia',
            None,
            (player.avatar if player.avatar else player.default_avatar).url
        )

        embed = utils.create_embed(title=question, author_field=author_field, content=text, color=discord.Color.teal())

        # calculate the timeout
        timeout = round(char_count / self.config['game']['chars_per_second'] +
                        self.config['game']['min_read_time'])

        embed.add_field(name=':stopwatch: Timeout:',
                        value=f'{timeout} seconds')
        embed.add_field(name=':book: Source:',
                        value=source)
        embed.add_field(name=':newspaper: Results of the last quiz:',
                        value='```\n ```',
                        inline=False)
        return embed, len(answers), correct_index, timeout

    def create_response(self, user, positive):
        msg = random.choice(self.config['compliments'] if positive else self.config['insults'])
        return msg.format(user.display_name)


async def setup(bot):
    await bot.add_cog(TriviaCog(bot))
