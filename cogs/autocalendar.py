from discord.ext import commands
from template_cog import LotrCog


class AutoCalendar(LotrCog):
    def __init__(self, bot):
        super().__init__(bot)


async def setup(bot):
    await bot.add_cog(AutoCalendar(bot))