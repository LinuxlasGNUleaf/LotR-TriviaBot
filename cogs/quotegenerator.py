import random

import discord
import yaml
from discord.ext import commands

import discord_utils as du
from template_cog import LotrCog


class QuoteGenerator(LotrCog):
    """
    Generates quotes with a specified set of people, using quotes from a large online database
    """

    def __init__(self, bot):
        super().__init__(bot)

    @du.category_check('minigames')
    @commands.command(aliases=['qgen', 'quotegen', 'story', 'sgen'])
    async def quote(self, ctx, *players):
        char_range = self.options['character_range']
        if len(players) not in range(char_range[0], char_range[1] + 1):
            await ctx.send(
                f':x: Please provide anywhere between {char_range[0]} and {char_range[1]} arguments / characters for the quote.')
            return

        title_str = f'{ctx.author.name}\'s story about '
        if len(players) == 1:
            title_str += players[0]
        else:
            title_str += ', '.join(players[:-1]) + ' and ' + players[-1]
        embed = discord.Embed()
        embed.set_author(name=title_str, icon_url=(ctx.author.avatar if ctx.author.avatar else ctx.author.default_avatar).url,
                         url=self.options['generator_url'])
        embed.set_footer(
            text='-' * 90 + '\nPlease check out the original generator (link is in title), it\'s pretty epic 😎')

        players = list(players)
        random.shuffle(players)

        quote = random.choice(self.get_quotes(
            len(players), self.options['include_nsfw']))
        embed.description = quote.format(*players, ast='*')
        await ctx.send(embed=embed)

    def get_quotes(self, num, nsfw):
        with open(self.assets['quotes'], 'r', encoding='utf-8') as qfile:
            questions = yaml.safe_load(
                qfile)[f'{self.options["num2word"][num]}Quotes']
        shipping_quotes = questions['shipping']
        non_shipping_quotes = questions['nonshipping']

        return_quotes = shipping_quotes['sfw'] + non_shipping_quotes['sfw']
        if nsfw:
            return_quotes += shipping_quotes['nsfw']
            return_quotes += non_shipping_quotes['nsfw']

        return return_quotes


async def setup(bot):
    await bot.add_cog(QuoteGenerator(bot))
