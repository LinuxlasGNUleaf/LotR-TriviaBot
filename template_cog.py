import logging

from discord.ext import commands

import backend_utils as bu
from discord_client import LotrBot


class LotrCog(commands.Cog):
    """
    The super class all cogs for this bot have to inherit from
    """

    def __init__(self, bot):
        self.bot: LotrBot
        self.dc_settings_cache: dict
        self.dc_settings_options: dict
        self.options: dict
        self.tokens: dict
        self.caches: dict
        self.caches_locations: dict
        self.assets: dict
        self.logger: logging.Logger

        self.bot: LotrBot = bot
        self.dc_settings_cache, self.dc_settings_options = (bot.caches['discord_settings'], bot.options['discord']['settings'])
        self.options = self.bot.load_config_for_cog(self.__cog_name__)
        self.tokens, self.caches, self.caches_locations, self.assets = self.bot.load_files_for_context(self.options,
                                                                                                       self.__cog_name__)
        self.bot.save_functions[self.__cog_name__] = self.save_caches
        self.logger = logging.getLogger(__name__)
        self.logger.level = logging.INFO

    def save_caches(self):
        bu.save_caches(self.caches, self.caches_locations, self.logger, self.__cog_name__)
