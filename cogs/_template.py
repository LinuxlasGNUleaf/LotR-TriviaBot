import logging
from discord.ext import commands

class REPLACE(commands.Cog):
    '''
    TEMPLATE DOCSTRING
    '''
    def __init__(self,bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.', self.__class__.__name__.title())

    #@commands.command()


async def setup(bot):
    await bot.add_cog(REPLACE(bot))
