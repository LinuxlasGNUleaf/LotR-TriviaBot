from datetime import datetime
import aiohttp
from discord.ext import commands
import discord

class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.json = []
        self.old_timestamp = datetime.now()
        self.default_query_size = self.bot.config['reddit']['query_limit']
        self.query_size = self.default_query_size
        self.json_timeout = self.bot.config['reddit']['json_timeout']
        self.sub_attributes = ['id','title','author','url','is_self','selftext','subreddit']
        self.sub_imgs = {}

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.__class__.__name__} Cog has been loaded.')

    @commands.command()
    async def meme(self, ctx):
        '''
        posts a LotR or Hobbit-related meme in the channel
        '''
        if ctx.channel.id not in self.bot.meme_cache.keys():
            self.bot.meme_cache[ctx.channel.id] = []

        difference = datetime.now() - self.old_timestamp

        if not self.json or difference.total_seconds()/60 > self.json_timeout:
            await self.refreshJSON()
            self.query_size = self.default_query_size
            self.old_timestamp = datetime.now()

        found_meme = False
        while not found_meme:
            for submission in self.json:
                if not submission['id'] in self.bot.meme_cache[ctx.channel.id]:
                    found_meme = True
                    self.bot.meme_cache[ctx.channel.id].append(submission['id'])
                    embed = discord.Embed(title=submission['title'])
                    embed.set_image(url=submission['url'])
                    embed.set_author(name='r/'+submission['subreddit'], icon_url=submission['sub_img'])
                    embed.url = 'https://www.reddit.com/'+submission['id']
                    embed.set_footer(text='Author: u/{:20} Subreddit: r/{:20}'.format(submission['author'],submission['subreddit']))
                    await ctx.send(embed=embed)
                    break
            self.query_size += self.default_query_size
            self.old_timestamp = datetime.now()
            await self.refreshJSON()

    async def refreshJSON(self):
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
