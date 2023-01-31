from discord.ext import commands

from template_cog import LotrCog


class BanRoulette(LotrCog):
    def __init__(self, bot):
        super().__init__(bot)


async def setup(bot):
    await bot.add_cog(BanRoulette(bot))
