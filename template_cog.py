import logging
from discord.ext import commands

import backend_utils as bu


class LotrCog(commands.Cog):
    """
    The super class all cogs for this bot have to inherit from
    """

    def __init__(self, bot):
        self.bot = bot
        self.dc_settings_cache, self.dc_settings = (bot.caches['discord_settings'], bot.options['discord']['settings'])
        self.options = self.bot.load_config_for_cog(self.__cog_name__)
        self.tokens, self.caches, self.caches_locations, self.assets = self.bot.load_files_for_context(self.options,
                                                                                                       self.__cog_name__)
        self.bot.save_functions[self.__cog_name__] = self.save_caches
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.', self.__class__.__name__.title())

    def save_caches(self):
        bu.save_caches(self.caches, self.caches_locations, self.logger, self.__cog_name__)
