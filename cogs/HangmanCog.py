import random
import string

import discord
from discord import app_commands

from src.CustomUIs import HangmanView
from src.DefaultCog import DefaultCog


class HangmanCog(DefaultCog, group_name='hangman'):
    """
    hangman game with ME-related characters and places
    """

    @app_commands.command(name='play')
    async def hangman(self, interaction: discord.Interaction):
        with open(self.assets['words'], 'r') as csvfile:
            word = random.choice(csvfile.readlines()).strip()
        HangmanView(interaction, self, word)


async def setup(bot):
    await bot.add_cog(HangmanCog(bot))
