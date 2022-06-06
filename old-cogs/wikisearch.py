from discord.ext import commands
from googlesearch import search

import discord_utils as du
from template_cog import LotrCog


class WikiSearch(LotrCog):
    """
    GoogleSearch integration for the Bot
    """

    def __init__(self, bot):
        super().__init__(bot)

    @du.category_check('lore')
    @commands.command(name='search')
    async def lotr_search(self, ctx, *, query):
        """
        searches on tolkiengateway.net for a given entry
        """
        site = self.options['site']
        content = list(search(f'{query} site:{site}', lang='en', num_results=1))

        if not content:
            await ctx.send(f':x: No results for `{query}` on  *{site}*.')
            return
        content = content[0]
        title = f':mag: 1st result for `{query}` on  *{site}* :'
        await ctx.send(embed=du.create_embed(title=title, content=content))


def setup(bot):
    bot.add_cog(WikiSearch(bot))
