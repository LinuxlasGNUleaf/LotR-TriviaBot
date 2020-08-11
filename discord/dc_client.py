'''
Main discord bot class, includes minigames.py for all the extra functionality
'''

from random import choice
import asyncio
import discord
import minigames

class LotrBot(discord.Client):
    '''
    Bot client, inheriting from discord.Client
    '''
    def __init__(self, config, scoreboard, settings,
                 reddit_client, yt_api_client, google_search_client):
        self.config = config
        self.scoreboard = scoreboard
        self.blocked = []
        self.do_autoscript = True
        self.script = []
        self.settings = settings
        self.script_condensed = []
        self.reddit_client = reddit_client
        self.yt_api_client = yt_api_client
        self.google_search_client = google_search_client
        minigames.parse_script(config.DISCORD_CONFIG['script.path'],
                               self.script, self.script_condensed)
        super().__init__()


    async def on_ready(self):
        '''
        init function for discord bot
        '''
        print('[INFO]: Setting rich presence...')
        await self.change_presence(activity=discord.Activity\
            (type=discord.ActivityType.watching,
             name=choice(self.config.DISCORD_CONFIG['custom_status'])))
        print('[SYSTEM]: online. All systems operational.')
        print('||>----------- O N L I N E ------------>||')


    async def on_message(self, message):
        '''
        main function to recognize a bot command
        '''
        if message.author == self.user or \
           message.author.id in self.blocked or \
           message.author.bot:
            return

        user = message.author
        raw_content = message.content.strip()
        content = raw_content.lower()
        channel = message.channel
        is_dm = isinstance(channel, discord.channel.DMChannel)
        if not is_dm:
            server = channel.guild
            if not channel.permissions_for(server.me).send_messages:
                return

#==============================================================================
        if content.startswith(self.config.GENERAL_CONFIG['key'] + ' config') and not is_dm:
            content = content.split(' ')[2:]
            for i, item in enumerate(content):
                content[i] = item.strip()
            if content[0] in self.config.DISCORD_CONFIG['settings.features']:
                ret = minigames.edit_settings(content, self.settings, channel)
                await channel.send(ret)
            elif content[0] == 'help':
                await channel.send(self.config.DISCORD_CONFIG['settings.help'])
            elif content[0] == 'show':
                await channel.send(embed=minigames.create_config_embed(channel,
                                                                       self.settings,
                                                                       self.config))
            else:
                await channel.send("Unknown Feature! Try one of the following:\n`"+ \
'`, `'.join(self.config.DISCORD_CONFIG['settings.features']+['help', 'show'])+'`')


#==============================================================================
        elif content == self.config.GENERAL_CONFIG['key'] + ' trivia' and \
             minigames.feature_allowed('trivia-quiz', channel, self.settings, self.config):

            # send the question message
            embed, correct_ind, len_answers = minigames.\
                create_trivia_question(user, self.scoreboard, self.config)
            await channel.send(embed=embed,
                               delete_after=self.config.DISCORD_CONFIG['trivia.timeout'])

            def check(chk_msg):
                return chk_msg.author == user and chk_msg.channel == channel

            self.blocked.append(user.id)
            try:
                msg = await self.wait_for('message',
                                          check=check,
                                          timeout=self.config.DISCORD_CONFIG['trivia.timeout'])
            except asyncio.TimeoutError:
                msg = ''
            self.blocked.remove(user.id)

            reply = minigames.create_trivia_reply(user, msg, self.scoreboard,
                                                  correct_ind, len_answers,
                                                  self.config)
            await channel.send(reply)

#==============================================================================
        elif content == self.config.GENERAL_CONFIG['key']+' hangman':
            embed, game_info = minigames.initiate_hangman_game(user, self.config)
            hangman_msg = await channel.send(embed=embed)

            def check(chk_msg):
                return chk_msg.author == user and chk_msg.channel == channel

            self.blocked.append(user.id)

            failed = False
            while not failed:
                try:
                    msg = await self.wait_for('message',
                                              check=check,
                                              timeout=self.config.DISCORD_CONFIG['hangman.timeout'])
                except asyncio.TimeoutError:
                    msg = ''

                embed, failed, message, game_info = minigames.\
                    update_hangman_game(user, msg, game_info, self.config)
                await hangman_msg.edit(embed=embed)
                if message:
                    await channel.send(message)

            self.blocked.remove(user.id)

#==============================================================================
        elif content == self.config.GENERAL_CONFIG['key'] + ' meme' and \
             minigames.feature_allowed('memes', channel, self.settings, self.config):
            async with channel.typing():
                ch_id = channel.id if is_dm else server.id
                embed = minigames.reddit_meme(ch_id,
                                              self.reddit_client,
                                              self.config.REDDIT_CONFIG['subreddit'])
                await channel.send(embed=embed)

#==============================================================================
        elif content == self.config.GENERAL_CONFIG['key'] + ' squote':
            embed = minigames.silmarillion_quote(self.config)
            await channel.send(embed=embed)

#==============================================================================
        elif content == self.config.GENERAL_CONFIG['key'] + ' profile' and \
             minigames.feature_allowed('trivia-quiz', channel, self.settings, self.config):
            if user.id in self.scoreboard.keys():
                await channel.send(embed=minigames.create_trivia_profile(user, self.scoreboard))
            else:
                await channel.send('You have to play a game of trivia before a \
profile can be generated! use `{} trivia` to take a quiz!'\
                                   .format(self.config.GENERAL_CONFIG['key']))

#==============================================================================
        elif content.startswith(self.config.GENERAL_CONFIG['key'] + ' yt ') and \
             minigames.feature_allowed('yt-search', channel, self.settings, self.config):
            async with channel.typing():
                raw_content = raw_content.split(self.config.GENERAL_CONFIG['key'] + ' yt ')[1]
                start, end = (-1, -1)
                query = ''

                start = raw_content.find('\"')
                if start != -1:
                    end = raw_content.find('\"', start + 1)
                    if end != -1:
                        query = raw_content[start+1:end]
                        if raw_content[:start].strip().isdigit():
                            num = max(1, int(raw_content[:start].strip()))
                        elif raw_content[end+1:].strip().isdigit():
                            num = max(1, int(raw_content[end+1:].strip()))
                        else:
                            num = 1

                if not query:
                    await channel.send(minigames.create_reply(user, True, self.config) +
                                       '\nTry providing a query next time!\nThe correct syntax is: \
`{0} yt "<keywords>" \n(you can also provide a video count, before or after the query)`\n'\
                                   .format(self.config.GENERAL_CONFIG['key']))
                    return

                result = minigames.search_youtube(
                    self.yt_api_client,
                    self.config.YT_CONFIG['channel_id'],
                    query,
                    num,
                    self.config)

                if not result:
                    await channel.send('*\'I have no memory of this place\'*\n\
    ~Gandalf\nYour query `{}` yielded no results!'.format(query))
                    return

                for embed in result:
                    await channel.send(embed=embed)

#==============================================================================
        elif content == self.config.GENERAL_CONFIG['key'] + ' help':
            embed = minigames.create_embed(
                title='LotR Trivia Bot help',
                content=self.config.DISCORD_CONFIG['help.text'],
                footnote=self.config.DISCORD_CONFIG['help.footer'])
            await channel.send(embed=embed)

#==============================================================================
        elif content == self.config.GENERAL_CONFIG['key'] + ' scoreboard' and \
             minigames.feature_allowed('trivia-quiz', channel, self.settings, self.config):
            if is_dm:
                await channel.send("Well that's not going to work, mate.\n\
You are in a DM Channel... join a server where this amazing bot is present to create a scoreboard.")
                return
            embed = minigames.create_scoreboard(self.scoreboard, server)
            await channel.send(embed=embed)

#==============================================================================
        elif content.startswith(self.config.GENERAL_CONFIG['key'] + ' search '):
            async with channel.typing():
                raw_content = ' '.join(raw_content.split(' ')[2:]).strip()
                result = minigames.lotr_search(self.google_search_client, raw_content, self.config)
                if isinstance(result, str):
                    await channel.send(result)
                else:
                    await channel.send(embed=result[0])
                    await channel.send(result[1])

#==============================================================================
        elif self.do_autoscript and not is_dm and \
             minigames.feature_allowed('autoscript', channel, self.settings, self.config):
            result = minigames.find_similar_from_script\
            (message.content, self.script_condensed, self.script)
            if isinstance(result, list):
                if channel.permissions_for(server.me).add_reactions:
                    await message.add_reaction('✅')
                for line in result:
                    await channel.send(line)
