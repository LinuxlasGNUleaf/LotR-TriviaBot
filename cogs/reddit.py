from datetime import datetime
import logging
import asyncio
from discord.ext import commands
import asyncpraw
import discord
from cogs import _dcutils


class Reddit(commands.Cog):
    '''
    handles the Reddit integration (JSON API) for the Bot
    '''

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.posts = []
        self.old_timestamp = datetime.now()
        self.default_query_size = self.bot.config['reddit']['query_limit']
        self.query_size = self.default_query_size
        self.subreddits = 0
        self.sub_thumbnails = {}
        self.reddit = asyncpraw.Reddit(
            client_id=self.bot.reddit_credentials[0],
            client_secret=self.bot.reddit_credentials[1],
            user_agent=self.bot.config['reddit']['useragent']
        )
        self.subreddit = 0
        # starting autofetching posts
        self.autofetch_task = asyncio.get_event_loop().create_task(self.auto_fetch())

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.',
                         self.__class__.__name__.title())

    def cog_unload(self):
        asyncio.get_event_loop().create_task(self.reddit.close())
        asyncio.get_event_loop().create_task(self.autofetch_task.close())

    @_dcutils.category_check('memes')
    @commands.command()
    @commands.cooldown(10, 10)
    async def meme(self, ctx):
        if not self.posts or (datetime.now() - self.old_timestamp).total_seconds()/60 > self.bot.config['reddit']['query_limit']:
            await self.refetch_posts()

        while True:
            for post in self.posts:
                if post.id in self.bot.meme_cache[ctx.channel.id]:
                    continue
                self.bot.meme_cache[ctx.channel.id].append(post.id)
                # processing meme, determinig whether it's an image or not, yada yada yada
                embed = discord.Embed(title=post.title if len(post.title) <= 256 else post.title[:253]+'...')
                ftype = post.url.split('.')[-1]
                if ftype in ['jpeg', 'jpg', 'gif', 'png'] or post.domain == 'i.redd.it':
                    embed.set_image(url=post.url)
                elif ftype in ['gifv', 'mp4', 'avi', 'webm', 'mov'] or post.domain == 'v.redd.it':
                    embed.set_thumbnail(
                        url=self.bot.config['reddit']['video_thumbnail'])
                embed.set_author(
                    name=post.subreddit_name_prefixed, icon_url=self.sub_thumbnails[post.subreddit_name_prefixed])
                embed.url = f'https://reddit.com{post.permalink}'
                embed.set_footer(text='Author: u/'+post.author.name)
                await ctx.send(embed=embed)
                break
            else:
                self.query_size += self.default_query_size
                await self.refetch_posts()
                continue
            break

    async def auto_fetch(self):
        '''
        autosave feature
        '''
        self.logger.info('Autofetching posts initialized.')
        while True:
            self.logger.info(datetime.now().strftime(
                'Autofetching new posts %X on %a %d/%m/%y'))
            self.query_size = self.default_query_size
            await self.refetch_posts()
            await asyncio.sleep(self.bot.config['reddit']['refresh_interval']*60)

    async def refetch_posts(self):
        for subreddit in self.bot.config['reddit']['subreddits']:
            if f'r/{subreddit}' not in self.sub_thumbnails:
                temp_sub = await self.reddit.subreddit(subreddit, fetch=True)
                self.sub_thumbnails[f'r/{subreddit}'] = temp_sub.icon_img
        self.subreddit = await self.reddit.subreddit('+'.join(self.bot.config['reddit']['subreddits']))
        self.posts = []
        async for submission in self.subreddit.hot(limit=self.query_size):
            self.posts.append(submission)
        self.old_timestamp = datetime.now()


def setup(bot):
    bot.add_cog(Reddit(bot))
