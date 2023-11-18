import logging

from discord.ext import commands

from src.DataManager import DataInterface
from src.LotrBot import LotrBot


class DefaultCog(commands.Cog):
    """
    The super class all cogs for this bot have to inherit from
    """

    def __init__(self, bot: LotrBot):
        self.bot: LotrBot = bot

        self.name = self.__cog_name__.lower().replace('cog','')
        # load cog config
        self.config: dict = bot.asset_mgr.load_config_for_cog(self.name)
        # load cog assets
        self.assets: dict = bot.asset_mgr.load_assets(working_config=self.config)
        # create tables and database interface for cog
        self.data: dict[str, DataInterface] = bot.data_mgr.setup_cog(self.name, self.config)
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.level = logging.INFO
