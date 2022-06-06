import discord
from discord.ext import commands
from googleapiclient.discovery import build

import backend_utils as bu
import discord_utils as du
from template_cog import LotrCog


class YoutubeSearch(LotrCog):
    """
    handles the YT-Data API integration of the Bot
    """

    def __init__(self, bot):
        super().__init__(bot)
        self.youtube = build('youtube',
                             'v3',
                             developerKey=self.bot.yt_credentials[0],
                             cache_discovery=False)

    @du.category_check('lore')
    @commands.command(name='ytsearch', aliases=['yt', 'yt-search', 'ysearch', 'youtube'])
    async def search_youtube(self, ctx, *query):
        """
        searches YouTube for videos by a specific channel
        """

        query = list(query)
        if query[-1].isdecimal():
            num = max(
                min(int(query[-1]), self.options['max_video_count']), 1)
            del query[-1]
        else:
            num = 1
        query = ' '.join(query)

        if not query:
            await ctx.send(
                f'\nTry providing a query next time! The correct syntax is: `{self.bot.options["discord"]["prefix"]} yt <keywords> (<number of results>)`')

        vid_request = self.youtube.search().list(
            q=query,
            channelId=self.bot.config['youtube']['channel_id'],
            part='snippet',
            type='video',
            maxResults=num
        ).execute()['items']

        if not vid_request:
            await ctx.send(f'*\'I have no memory of this place\'* ~Gandalf\nYour query `{query}` yielded no results!')
            return

        for i, video in enumerate(vid_request):
            embed = discord.Embed(
                title=video['snippet']['title'],
                url=f'https://www.youtube.com/watch?v={video["id"]["videoId"]}'
            )
            vid_info = self.youtube.videos().list(part='snippet,statistics',
                                                  id=video['id']['videoId']).execute()['items'][0]

            embed.set_author(name=f'🔍 {bu.ordinal(i + 1)} Search Result')
            embed.set_image(url=video['snippet']['thumbnails']['medium']['url'])

            description = ''
            for line in vid_info['snippet']['description'].split('\n'):
                line = line.strip().lower()
                if not line:
                    continue
                for item in self.options['desc_blacklist']:
                    if item in line:
                        break
                else:
                    description += line + '\n'

            embed.description = description.strip()
            embed.set_footer(text='Published: ' + '/'.join(video['snippet']['publishedAt'][:10].split('-')[::-1]))
            embed.add_field(name=':play_pause: Views:', value=f'{int(vid_info["statistics"]["viewCount"]):,}',
                            inline=True)
            embed.add_field(name=':thumbsup: Likes:', value=f'{int(vid_info["statistics"]["likeCount"]):,}',
                            inline=True)
            embed.add_field(name=':speech_balloon: Comments:', value=f'{int(vid_info["statistics"]["commentCount"]):,}',
                            inline=True)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(YoutubeSearch(bot))
