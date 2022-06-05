import random
import string
from datetime import datetime

import discord
import inflect
from discord.ext import commands
from word2number import w2n

from template_cog import LotrCog


class AutoGimli(LotrCog):
    """
    handles the AutoGimli integration of the Bot
    """

    def __init__(self, bot):
        super().__init__(bot)
        self.inflect = inflect.engine()
        self.cooldown_list = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.',
                         self.__class__.__name__.title())

    @commands.Cog.listener('on_message')
    async def autogimli(self, msg):
        if random.randint(0, self.options['chance'] - 1) != 0:
            return
        if msg.author.bot or msg.embeds or msg.attachments or msg.author.id in self.bot.blocked:
            return
        perms = msg.guild.me.permissions_in(msg.channel)

        if msg.author.id in self.cooldown_list:
            if (datetime.now() - self.cooldown_list[msg.author.id]).total_seconds() < self.options['cooldown']:
                return

        if isinstance(msg.channel, discord.channel.DMChannel):
            return
        if not msg.channel.permissions_for(msg.channel.guild.me).send_messages:
            return

        content = msg.content.split(' ')
        for word in content:
            word = ''.join(filter(lambda x: x in string.digits, word.strip()))
            if word.isdigit():
                if int(word) in range(*self.options['interval']):
                    gimli_count = int(word.strip())
                    break
        else:
            try:
                content = ' '.join(content)
                for char in string.punctuation:
                    if char == '-':
                        continue
                    content = content.replace(char, ' ')
                gimli_count = w2n.word_to_num(content.strip())
                if not (float(gimli_count).is_integer()) or gimli_count not in range(*self.options['interval']):
                    return
            except ValueError:
                return

        if perms.add_reactions:
            for reaction in self.options['special_reactions'].setdefault(msg.guild.id, []):
                try:
                    await msg.add_reaction(reaction)
                except discord.errors.HTTPException:
                    pass

        if gimli_count == 2 and self.options['number_two_special_message']:
            await msg.channel.send('That still only counts as one!')
        else:
            await msg.channel.send(
                f'{self.inflect.number_to_words(gimli_count).title()}? Oh, that\'s not bad for a pointy-eared elvish princeling. Hmph! I myself am sitting pretty on **{self.inflect.number_to_words(gimli_count + 1).upper()}**!')
        self.cooldown_list[msg.author.id] = datetime.now()


async def setup(bot):
    await bot.add_cog(AutoGimli(bot))
