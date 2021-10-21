import logging
import random
from discord.ext import commands
import discord
import inflect
import string
from datetime import datetime
from word2number import w2n


class Autogimli(commands.Cog):
    '''
    handles the Autogimli integration of the Bot
    '''
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.inflect = inflect.engine()
        self.cooldown_list = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.',
                         self.__class__.__name__.title())

    @commands.cooldown(10, 10)
    @commands.Cog.listener('on_message')
    async def autogimli(self, msg):
        if random.randint(0, self.bot.config['discord']['autogimli']['chance']-1) != 0:
            return
        if msg.author.bot or msg.embeds or msg.attachments or msg.author.id in self.bot.blocked:
            return

        if msg.author.id in self.cooldown_list:
            if (datetime.now() - self.cooldown_list[msg.author.id]).total_seconds() < self.bot.config['discord']['autogimli']['cooldown']:
                return

        if isinstance(msg.channel, discord.channel.DMChannel):
            return
        if not msg.channel.permissions_for(msg.channel.guild.me).send_messages:
            return

        content = msg.content.split(' ')
        for word in content:
            word = ''.join(filter(lambda x: x in string.digits,word.strip()))
            if word.isdigit():
                if int(word) in range(*self.bot.config['discord']['autogimli']['interval']):
                    gimli_count = int(word.strip())
                    break
        else:
            try:
                content = ' '.join(content)
                for char in string.punctuation:
                    if char == '-':
                        continue
                    content = content.replace(char,' ')
                gimli_count = w2n.word_to_num(content.strip())
                if not(float(gimli_count).is_integer()) or gimli_count not in range(*self.bot.config['discord']['autogimli']['interval']):
                    return
            except ValueError:
                return


        if msg.guild.id in self.bot.config['discord']['autogimli']['special_reactions']:
            try:
                await msg.add_reaction(self.bot.config['discord']['autogimli']['special_reactions'][msg.guild.id])
            except discord.errors.HTTPException:
                pass

        if gimli_count == 2 and self.bot.config['discord']['autogimli']['number_two_special_message']:
            await msg.channel.send('That still only counts as one!')
        else:
            await msg.channel.send(f'{self.inflect.number_to_words(gimli_count).title()}? Oh, that\'s not bad for a pointy-eared elvish princeling. Hmph! I myself am sitting pretty on **{self.inflect.number_to_words(gimli_count+1).upper()}**!')
        self.cooldown_list[msg.author.id] = datetime.now()

def setup(bot):
    bot.add_cog(Autogimli(bot))
