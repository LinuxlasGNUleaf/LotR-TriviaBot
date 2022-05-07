import asyncio
import logging
from datetime import datetime

import asyncpraw
import discord
from discord.ext import commands, tasks

import dc_utils


class Reddit(commands.Cog):
    """
    handles the Reddit integration (JSON API) for the Bot
    """

    def __init__(self, bot):
        self.bot = bot
        self.options = self.bot.config['reddit']
        self.logger = logging.getLogger(__name__)
        self.posts = []
        self.old_timestamp = datetime.now()
        self.query_size = self.options['default_query_size']
        self.query_multiplier = 1
        self.subreddits = 0
        self.sub_thumbnails = {}
        self.reddit = asyncpraw.Reddit(
            client_id=self.bot.tokens['reddit'][0],
            client_secret=self.bot.tokens['reddit'][1],
            user_agent=self.options['useragent']
        )
        self.subreddit = 0

        self.get_post_lock = asyncio.Lock()

        self.auto_refresh.change_interval(minutes=self.options['refresh_interval'])
        self.auto_refresh.start()

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.',
                         self.__class__.__name__.title())

    def cog_unload(self):
        asyncio.get_event_loop().create_task(self.reddit.close())

    @dc_utils.category_check('memes')
    @commands.command()
    @commands.cooldown(10, 10)
    async def meme(self, ctx):
        # processing meme, determining whether it's an image or not, yada yada yada
        post = await self.get_post(ctx.channel.id)
        embed = discord.Embed(title=post.title if len(post.title) <= 256 else post.title[:253] + '...')
        file_type = post.url.split('.')[-1]
        if file_type in ['jpeg', 'jpg', 'gif', 'png'] or post.domain == 'i.redd.it':
            embed.set_image(url=post.url)
        elif file_type in ['gifv', 'mp4', 'avi', 'webm', 'mov'] or post.domain == 'v.redd.it':
            embed.set_thumbnail(
                url=self.options['video_thumbnail'])
        embed.set_author(
            name=post.subreddit_name_prefixed, icon_url=self.sub_thumbnails[post.subreddit_name_prefixed])
        embed.url = f'https://reddit.com{post.permalink}'
        embed.set_footer(text='Author: u/' + post.author.name)
        await ctx.send(embed=embed)

    @tasks.loop()
    async def auto_refresh(self):
        self.logger.debug('Reloading posts...')

        # reset query size
        self.query_multiplier = 1
        await self.refresh_posts()

    @auto_refresh.before_loop
    async def before_reload(self):
        self.logger.info('Preloading posts for the first time...')
        await self.refresh_posts()
        self.logger.info('Preloading done.')

    async def refresh_posts(self):
        # acquire sub thumbnails if not present
        for subreddit in self.options['subreddits']:
            if f'r/{subreddit}' not in self.sub_thumbnails:
                temp_sub = await self.reddit.subreddit(subreddit, fetch=True)
                self.sub_thumbnails[f'r/{subreddit}'] = temp_sub.icon_img

        self.posts = []
        self.subreddit = await self.reddit.subreddit('+'.join(self.options['subreddits']))

        async for submission in self.subreddit.hot(limit=self.query_size):
            self.posts.append(submission)
        self.old_timestamp = datetime.now()

    async def get_post(self, channel_id):
        async with self.get_post_lock:
            valid_post = None
            while not valid_post:
                for post in self.posts:
                    if post.id not in self.bot.meme_cache[channel_id]:
                        self.bot.meme_cache[channel_id].append(post.id)
                        return post

                self.logger.info('Reloading subreddits due to lack of new submissions.')
                self.query_multiplier += 1
                await self.refresh_posts()
                self.logger.info('Done reloading (for new submissions).')


async def setup(bot):
    await bot.add_cog(Reddit(bot))
