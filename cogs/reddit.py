import asyncio
from datetime import datetime

import asyncpraw
import discord
from discord.ext import commands, tasks

import discord_utils as du
from template_cog import LotrCog


class Reddit(LotrCog):
    """
    handles the Reddit integration (JSON API) for the Bot
    """

    def __init__(self, bot):
        super().__init__(bot)

        self.posts = []
        self.old_timestamp = datetime.now()
        self.query_size = self.options['default_query_size']
        self.query_multiplier = 1

        self.sub_thumbnails = {}
        self.reddit = None
        self.subreddit = None
        self.get_post_lock = asyncio.Lock()

    def cog_load(self):
        self.reddit = asyncpraw.Reddit(
            client_id=self.tokens['reddit'][0],
            client_secret=self.tokens['reddit'][1],
            user_agent=self.options['useragent']
        )
        self.subreddit = None
        self.auto_refresh.change_interval(minutes=self.options['refresh_interval'])
        self.auto_refresh.start()

    async def cog_unload(self):
        await self.reddit.close()
        self.auto_refresh.stop()

    @du.category_check('memes')
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
            name=post.subreddit_name_prefixed, icon_url=self.sub_thumbnails[post.subreddit_name_prefixed.lower()])
        embed.url = f'https://reddit.com{post.permalink}'
        embed.set_footer(text='Author: u/' + post.author.name)
        await ctx.send(embed=embed)

    @tasks.loop()
    async def auto_refresh(self):
        self.logger.debug('Auto-reloading posts...')

        # reset query size
        self.query_multiplier = 1
        await self.refresh_posts()

    @auto_refresh.before_loop
    async def before_refresh(self):
        self.logger.info('Preloading posts before starting to autorefresh...')
        async with self.get_post_lock:
            await self.refresh_posts()
        self.logger.info('Preloading of posts done.')
        await asyncio.sleep(self.options['refresh_interval'] * 60)

    async def refresh_posts(self):
        # acquire sub thumbnails if not present
        for subreddit in self.options['subreddits']:
            if f'r/{subreddit.lower()}' not in self.sub_thumbnails:
                temp_sub = await self.reddit.subreddit(subreddit, fetch=True)
                self.sub_thumbnails[f'r/{subreddit.lower()}'] = temp_sub.icon_img

        self.posts = []
        self.subreddit = await self.reddit.subreddit('+'.join(self.options['subreddits']))

        self.logger.info(f'Fetching the top {self.query_size * self.query_multiplier} hot submissions.')
        async for submission in self.subreddit.hot(limit=self.query_size * self.query_multiplier):
            self.posts.append(submission)
        self.old_timestamp = datetime.now()

    async def get_post(self, channel_id):
        if channel_id not in self.caches['post_cache']:
            self.caches['post_cache'][channel_id] = []
        async with self.get_post_lock:
            valid_post = None
            while not valid_post:
                for post in self.posts:
                    if post.id not in self.caches['post_cache'][channel_id]:
                        self.caches['post_cache'][channel_id].append(post.id)
                        return post

                self.logger.info('Reloading subreddits due to lack of new submissions.')
                self.query_multiplier += 1
                await self.refresh_posts()
                self.logger.info('Done reloading (for new submissions).')


async def setup(bot):
    await bot.add_cog(Reddit(bot))
