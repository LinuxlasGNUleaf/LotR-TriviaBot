from datetime import datetime
import logging
import aiohttp
from discord.ext import commands
import discord

class Reddit(commands.Cog):
    '''
    handles the Reddit integration (JSON API) for the Bot
    '''
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.json = []
        self.old_timestamp = datetime.now()
        self.default_query_size = self.bot.config['reddit']['query_limit']
        self.query_size = self.default_query_size
        self.json_timeout = self.bot.config['reddit']['json_timeout']
        self.sub_attributes = ['id','title','author','url','is_self','selftext','subreddit']
        self.sub_imgs = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.', self.__class__.__name__.title())

    @commands.command()
    @commands.cooldown(5,10)
    async def meme(self, ctx):
        '''
        posts a LotR or Hobbit-related meme in the channel
        '''
        if ctx.channel.id not in self.bot.meme_cache.keys():
            self.bot.meme_cache[ctx.channel.id] = []

        difference = datetime.now() - self.old_timestamp

        if not self.json or difference.total_seconds()/60 > self.json_timeout:
            await self.refresh_json()
            self.query_size = self.default_query_size
            self.old_timestamp = datetime.now()

        found_meme = False
        while not found_meme:
            for submission in self.json:
                if not submission['id'] in self.bot.meme_cache[ctx.channel.id]:
                    found_meme = True
                    self.bot.meme_cache[ctx.channel.id].append(submission['id'])
                    embed = discord.Embed(title=submission['title'])
                    ftype = submission['url'].split('.')[-1]
                    if ftype in ['jpeg','jpg','gif','png'] or 'i.redd.it' in submission['url']:
                        embed.set_image(url=submission['url'])
                    elif 'v.redd.it' in submission['url']:
                        embed.set_thumbnail(url=self.bot.config['reddit']['video_thumbnail'])
                    embed.set_author(name='r/'+submission['subreddit'], icon_url=submission['sub_img'])
                    embed.url = 'https://www.reddit.com/'+submission['id']
                    embed.set_footer(text='Author: u/'+submission['author'])
                    await ctx.send(embed=embed)
                    break
            self.query_size += self.default_query_size
            self.old_timestamp = datetime.now()
            await self.refresh_json()

    async def refresh_json(self):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://www.reddit.com/r/{}/hot.json?limit={}'.format('+'.join(self.bot.config['reddit']['subreddits']),self.query_size)) as result:
                self.json = []
                for submission in (await result.json())['data']['children']:
                    temp = {k:v for k,v in submission['data'].items() if k in self.sub_attributes}
                    if temp['subreddit'] in self.sub_imgs.keys():
                        temp['sub_img'] = self.sub_imgs[temp['subreddit']]
                    else:
                        async with session.get('https://www.reddit.com/r/{}/about.json'.format(temp['subreddit'])) as sub_info:
                            temp['sub_img'] = (await sub_info.json())['data']['icon_img']
                            self.sub_imgs[temp['subreddit']] = temp['sub_img']
                    self.json.append(temp)


def setup(bot):
    bot.add_cog(Reddit(bot))
