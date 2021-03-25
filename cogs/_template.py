from discord.ext import commands


class REPLACE(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.__class__.__name__} Cog has been loaded.')

    #@commands.command()


def setup(bot):
    bot.add_cog(REPLACE(bot))