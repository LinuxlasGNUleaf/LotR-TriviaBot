import logging
from discord.ext import commands


class LotrCog(commands.Cog):
    """
    TEMPLATE DOCSTRING
    """

    def __init__(self, bot):
        self.bot = bot
        self.options = self.bot.load_config_for_cog(self.__cog_name__)
        self.tokens, self.caches, self.assets = self.bot.load_files_for_context(self.options, self.__cog_name__)
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.', self.__class__.__name__.title())

    # @commands.command()


async def setup(bot):
    await bot.add_cog(REPLACE(bot))
