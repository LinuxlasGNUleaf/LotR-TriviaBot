'''
Main discord bot class, includes minigames.py for all the extra functionality
'''

import random
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
            await minigames.create_trivia_quiz(channel,
                                               self,
                                               user,
                                               self.settings,
                                               self.config,
                                               self.blocked,
                                               self.scoreboard)

#==============================================================================
        elif self.is_command(content, 'hangman'):
            await minigames.create_hangman_game(channel,
                                                self,
                                                user,
                                                self.settings,
                                                self.config,
                                                self.blocked)

#==============================================================================
        elif self.is_command(content, 'meme'):
            await minigames.reddit_meme(channel,
                                        self.reddit_client,
                                        self.config.REDDIT_CONFIG['subreddit'],
                                        self.config,
                                        self.settings)

#==============================================================================
        elif self.is_command(content, 'squote') and \
             minigames.feature_allowed('squote', channel, self.settings, self.config):
            embed = minigames.silmarillion_quote(self.config)
            await channel.send(embed=embed)

#==============================================================================
        elif self.is_command(content, 'profile'):
            await minigames.display_profile(channel,
                                            user,
                                            self.settings,
                                            self.config,
                                            self.scoreboard)

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
        elif self.is_command(content, 'fight') and not is_dm:
            await minigames.lotr_battle(channel,
                                        self,
                                        user,
                                        content,
                                        self.config)

#==============================================================================
        elif self.do_autoscript and not is_dm:
            await minigames.find_similar_from_script(channel,
                                                     message,
                                                     self.script_condensed,
                                                     self.script,
                                                     self.settings,
                                                     self.config)
