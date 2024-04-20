import asyncio
import csv
import math
import random
import warnings
import io

import discord
import numpy as np
from typing import Optional
from discord import app_commands
from matplotlib import pyplot as plt

from src import utils, DataManager
from src.DefaultCog import DefaultCog


class BirthdayCog(DefaultCog, group_name='birthday'):
    """
    birthday (de)registration, calendar download and automatic notifications
    """

    @app_commands.command(name='get')
    @app_commands.describe(user='the user you want to get the birthday of')
    async def birthday(self, interaction: discord.Interaction, user: Optional[discord.Member]):
        pass

    @app_commands.command(name='register')
    async def register(self, interaction: discord.Interaction, month: Optional[int], day: Optional[int]):
        pass

    @app_commands.command(name='delete')
    async def delete(self, interaction: discord.Interaction):
        pass

    @app_commands.command(name='download')
    async def download(self, interaction: discord.Interaction):
        pass


async def setup(bot):
    await bot.add_cog(BirthdayCog(bot))
