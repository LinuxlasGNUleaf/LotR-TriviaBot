import logging
import random
import discord
from datetime import datetime
from discord.ext import commands
from difflib import SequenceMatcher

class AutoRepost(commands.Cog):
    '''
    activates whenever someone says "repost"
    '''
    def __init__(self,bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.cooldown_list = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.', self.__class__.__name__.title())

    @commands.cooldown(1, 120)
    @commands.Cog.listener('on_message')
    async def autorepost(self, msg):
        if msg.author.bot or msg.embeds or msg.attachments or msg.author.id in self.bot.blocked:
            return
        perms = msg.guild.me.permissions_in(msg.channel)
        if not (perms.send_messages and perms.attach_files and perms.embed_links):
            return
        
        if msg.guild.id not in self.bot.config['discord']['autorepost']['servers']:
            return
        
        if msg.author.id in self.cooldown_list:
            if (datetime.now() - self.cooldown_list[msg.author.id]).total_seconds() < self.bot.config['discord']['autorepost']['cooldown']:
                return

        
        words = msg.content.split(' ')
        for word in words:
            word = word.lower().strip()
            for trigger_word in self.bot.config['discord']['autorepost']['trigger_words']:
                if SequenceMatcher(None, word, trigger_word).ratio() >= self.bot.config['discord']['autorepost']['threshold']:
                    text = '🚨"REPOST" REPOST ALERT🚨'
                    image = random.choice(self.bot.config['discord']['autorepost']['media'])
                    self.cooldown_list[msg.author.id] = datetime.now()
                    if msg.channel.slowmode_delay:
                        await msg.reply(f'{text}\n{image}')
                    else:
                        await msg.reply(text)
                        await msg.channel.send(image)
                    if perms.add_reactions:
                        reactions = self.bot.config['discord']['autorepost']['reactions'] + self.bot.config['discord']['autorepost']['special_reactions'].setdefault(msg.guild.id,[])
                        for reaction in random.sample(reactions,random.randint(1,len(reactions)-1)):
                            try:
                                await msg.add_reaction(reaction)
                            except discord.errors.HTTPException:
                                pass
                    break


def setup(bot):
    bot.add_cog(AutoRepost(bot))
