from discord.ext import commands
from googlesearch import search
import cogs

class WikiSearch(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.__class__.__name__} Cog has been loaded.')

    @commands.command(name='search')
    async def lotr_search(self, ctx, *, query):
        '''
        searches on tolkiengateway.net for a given entry
        '''
        site = self.bot.config['google']['site']
        content = list(search(f'{query} site:{site}', lang='en', num_results=1))

        if not content:
            await ctx.send(':x: No results for `{}` on  *{}*.'.format(query, site))
            return
        content = content[0]
        title = f':mag: 1st result for `{query}` on  *{site}* :'
        await ctx.send(embed=cogs._dcutils.create_embed(title=title, content=content))

def setup(bot):
    bot.add_cog(WikiSearch(bot))
