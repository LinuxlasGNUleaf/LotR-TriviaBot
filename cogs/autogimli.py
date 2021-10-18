import logging
import string
from discord.ext import commands
import discord
import inflect
from word2number import w2n


class Autogimli(commands.Cog):
    '''
    handles the Autogimli integration of the Bot
    '''
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.allowed = string.ascii_letters + string.digits + ' '
        self.inflect = inflect.engine()

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.',
                         self.__class__.__name__.title())

    @commands.Cog.listener('on_message')
    async def autoscript(self, msg):
        if msg.author.bot:
            return

        if isinstance(msg.channel, discord.channel.DMChannel):
            return
        if not msg.channel.permissions_for(msg.channel.guild.me).send_messages:
            return

        content = ''.join(list(filter(lambda x: x in self.allowed,msg.content)))

        try:
            gimli_count = w2n.word_to_num(content)
        except ValueError:
            return

        if not(float(gimli_count).is_integer()) or gimli_count <= 2:
            return

        if msg.guild.id == '566219783377518592':
            try:
                await msg.add_reaction('Gumli:596753586147426355')
            except discord.errors.HTTPException:
                pass

        await msg.channel.send(f'{self.inflect.number_to_words(gimli_count).title()}? Oh, that\'s not bad for a pointy-eared elvish princeling. Hmph! I myself am sitting pretty on **{self.inflect.number_to_words(gimli_count+1).upper()}**!')


def setup(bot):
    bot.add_cog(Autogimli(bot))
