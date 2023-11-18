import logging

from discord.ext import commands
from LotrBot import LotrBot


class LotrCog(commands.Cog):
    """
    The super class all cogs for this bot have to inherit from
    """

    def __init__(self, bot: LotrBot):
        self.bot: LotrBot = bot

        # load cog config
        self.config: dict = bot.asset_mgr.load_config_for_cog(self.__cog_name__)
        # load cog assets
        self.assets: dict = bot.asset_mgr.load_assets(working_config=self.config)
        # create tables and database interface for cog
        self.data = bot.db_mgr.setup_cog(self.__cog_name__, self.config)

        self.logger: logging.Logger
        self.logger = logging.getLogger(__name__)
        self.logger.level = logging.INFO
