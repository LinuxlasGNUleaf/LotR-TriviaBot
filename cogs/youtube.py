from discord.ext import commands
from googleapiclient.discovery import build
import discord
import cogs

class YoutubeSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.youtube = build('youtube', 'v3', developerKey=self.bot.yt_credentials[0])

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.__class__.__name__} Cog has been loaded.')

    @commands.command(name='ytsearch',aliases=['yt','yt-search','ysearch','youtube'])
    async def search_youtube(self, ctx, *query):
        '''
        returns a give number of Youtube Video embeds for a specific channel
        '''
        query = list(query)
        if query[-1].isdecimal():
            num = max(min(int(query[-1]),self.bot.config['youtube']['max_video_count']),1)
            del query[-1]
        else:
            num = 1
        query = ' '.join(query)

        if not query:
            await ctx.send('\nTry providing a query next time! The correct syntax is: `{} yt <keywords> (<number of results>)`'.format(self.bot.config['general']['key']))

        vid_request = self.youtube.search().list(
            q=query,
            channelId=self.bot.config['youtube']['channel_id'],
            part='snippet',
            type='video',
            maxResults=num
        ).execute()['items']

        if not vid_request:
            await ctx.send('*\'I have no memory of this place\'* ~Gandalf\nYour query `{}` yielded no results!'.format(query))
            return
        
        for i, video in enumerate(vid_request):
            embed = discord.Embed(
                title=video['snippet']['title'],
                url='https://www.youtube.com/watch?v={}'.format(video['id']['videoId'])
            )
            vid_info = self.youtube.videos().list(part='snippet,statistics', id=video['id']['videoId']).execute()['items'][0]

            embed.set_author(name='🔍 {} Search Result'.format(cogs._dcutils.ordinal(i+1)))
            embed.set_image(url=video['snippet']['thumbnails']['medium']['url'])

            description = ''
            for line in vid_info['snippet']['description'].split('\n'):
                line = line.strip().lower()
                if not line:
                    continue
                for item in self.bot.config['youtube']['desc_blacklist']:
                    if item in line:
                        break
                else:
                    description += line+'\n'

            embed.description = description.strip()
            embed.set_footer(text=('Published: ' + '/'.join(video['snippet']['publishedAt'][:10].split('-')[::-1])))
            embed.add_field(name=':play_pause: Views:', value='{:,}'.format(int(vid_info['statistics']['viewCount'])), inline=True)
            embed.add_field(name=':thumbsup: Likes:', value='{:,}'.format(int(vid_info['statistics']['likeCount'])), inline=True)
            embed.add_field(name=':speech_balloon: Comments:', value='{:,}'.format(int(vid_info['statistics']['commentCount'])), inline=True)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(YoutubeSearch(bot))
