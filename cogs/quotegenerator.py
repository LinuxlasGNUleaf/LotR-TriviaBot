import logging
import random
import yaml
import discord
from discord.ext import commands
from cogs import _dcutils


class QuoteGenerator(commands.Cog):
    '''
    Generates quotes with a specified set of people, using quotes from a large online database
    '''

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.',
                         self.__class__.__name__.title())

    @_dcutils.category_check('minigames')
    @commands.command(aliases=['qgen', 'quotegen','story','sgen'])
    async def quote(self, ctx, *players):
        char_range = self.bot.config['discord']['quotegen']['character_range']
        if len(players) not in range(char_range[0],char_range[1]+1):
            await ctx.send(f':x: Please provide anywhere between {char_range[0]} and {char_range[1]} arguments / characters for the quote.')
            return

        title_str = f'{ctx.author.name}\'s story about '
        if len(players) == 1:
            title_str += players[0]
        else:
            title_str += ', '.join(players[:-1]) + ' and '+players[-1]
        embed = discord.Embed()
        embed.set_author(name=title_str, icon_url=ctx.author.avatar_url, url=self.bot.config['discord']['quotegen']['generator_url'])
        embed.set_footer(text='-'*100+'\nPlease check out the original generator (link is in title), it\'s pretty epic 😎')

        players = list(players)
        random.shuffle(players)

        quote = random.choice(self.get_quotes(
            len(players), self.bot.config['discord']['quotegen']['include_nsfw']))
        embed.description = quote.format(*players, ast='*')
        await ctx.send(embed=embed)

    def get_quotes(self, num, nsfw):
        with open('quotes.yaml', 'r', encoding='utf-8') as qfile:
            questions = yaml.safe_load(
                qfile)[f'{self.bot.config["discord"]["quotegen"]["num2word"][num]}Quotes']
        shipping_quotes = questions['shipping']
        nonshipping_quotes = questions['nonshipping']

        return_quotes = shipping_quotes['sfw'] + nonshipping_quotes['sfw']
        if nsfw:
            return_quotes += shipping_quotes['nsfw']
            return_quotes += nonshipping_quotes['nsfw']

        return return_quotes


async def setup(bot):
    await bot.add_cog(QuoteGenerator(bot))
