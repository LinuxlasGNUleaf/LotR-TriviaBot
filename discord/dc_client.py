'''
Main discord bot class, includes minigames.py for all the extra functionality
'''

import random
import asyncio
import discord
import minigames

class LotrBot(discord.Client):
    '''
    Bot client, inheriting from discord.Client
    '''
    def __init__(self, config, scoreboard, settings, reddit_client,
                 yt_api_client, google_search_client):
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

    def is_command(self, msg, cmdlet):
        '''
        checks whether a given message is a command
        '''
        return msg.startswith(self.config.GENERAL_CONFIG['key'] + ' ' + cmdlet)

    async def on_ready(self):
        '''
        init function for discord bot
        '''
        print('[INFO]: Setting rich presence...')
        await self.change_presence(activity=discord.Activity\
            (type=discord.ActivityType.watching,
             name=random.choice(self.config.DISCORD_CONFIG['custom_status'])))
        print('[SYSTEM]: online. All systems operational.')
        print('||>----------- O N L I N E ------------>||')


    async def on_message(self, message):
        '''
        main function to recognize a bot command
        '''
        user = message.author

        if user == self.user or user.id in self.blocked or user.bot:
            return
        raw_content = message.content.strip()
        content = raw_content.lower()
        channel = message.channel
        is_dm = isinstance(channel, discord.channel.DMChannel)
        if not is_dm:
            server = channel.guild
            if not channel.permissions_for(server.me).send_messages:
                return

#==============================================================================
        if self.is_command(content, 'config') and not is_dm:
            await minigames.manage_config(channel,
                                          user,
                                          content,
                                          self.config,
                                          self.settings)

#==============================================================================
        elif self.is_command(content, 'trivia'):
            await minigames.trivia_question(channel)


#==============================================================================
        elif self.is_command(content, 'hangman') and \
             minigames.feature_allowed('hangman', channel, self.settings, self.config):
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
        elif self.is_command(content, 'meme') and \
             minigames.feature_allowed('memes', channel, self.settings, self.config):
            ch_id = channel.id if is_dm else server.id
            embed = minigames.reddit_meme(ch_id,
                                          self.reddit_client,
                                          self.config.REDDIT_CONFIG['subreddit'])
            await channel.send(embed=embed)

#==============================================================================
        elif self.is_command(content, 'squote') and \
             minigames.feature_allowed('squote', channel, self.settings, self.config):
            embed = minigames.silmarillion_quote(self.config)
            await channel.send(embed=embed)

#==============================================================================
        elif self.is_command(content, 'profile') and \
             minigames.feature_allowed('trivia-quiz', channel, self.settings, self.config):
            if user.id in self.scoreboard.keys():
                await channel.send(embed=minigames.create_trivia_profile(user, self.scoreboard))
            else:
                await channel.send('You have to play a game of trivia before a \
profile can be generated! use `{} trivia` to take a quiz!'\
                                   .format(self.config.GENERAL_CONFIG['key']))

#==============================================================================
        elif self.is_command(content, 'yt '):
            await minigames.search_youtube(channel,
                                           user,
                                           raw_content,
                                           self.yt_api_client,
                                           self.config,
                                           self.settings)

#==============================================================================
        elif self.is_command(content, 'help'):
            await minigames.display_help(channel,
                                         self.config)

#==============================================================================
        elif self.is_command(content, 'scoreboard') and not is_dm:
            await minigames.display_scoreboard(channel,
                                               server,
                                               self.settings,
                                               self.config,
                                               self.scoreboard)

#==============================================================================
        elif self.is_command(content, 'search '):
            await minigames.lotr_search(channel,
                                        self.google_search_client,
                                        raw_content,
                                        self.config)

#==============================================================================
        elif self.is_command(content, 'fight'):
            await minigames.lotr_battle(self,
                                        channel,
                                        user,
                                        content)

#==============================================================================
        elif self.do_autoscript and not is_dm and \
             minigames.feature_allowed('autoscript', channel, self.settings, self.config):
            result = minigames.find_similar_from_script\
            (message.content, self.script_condensed, self.script, self.config)
            if result:
                try:
                    if channel.permissions_for(server.me).add_reactions:
                        await message.add_reaction('✅')
                    await channel.send(result)
                except discord.errors.Forbidden:
                    print('Encountered Forbidden error when adding Reaction!\nServer:{}\nChannel:{}\
\nMessage:{}\nUser:{}'.format(server, channel, content, user))
