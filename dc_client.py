import pickle
import os
import logging
import random
import asyncio
from datetime import datetime
import discord
from discord.ext import commands

class LotrBot(commands.Bot):
    '''
    The LotR-Bot. Subclass of discord.ext.commands.Bot
    '''
    def __init__(self, config):
        self.started = False
        self.logger = logging.getLogger(__name__)
        # evaluating cache directory
        config['general']['cache_path'] = os.path.expandvars(config['general']['cache_path'])

        self.config = config

        # updating the cache directories
        config['discord']['trivia']['cache'] = self.update_cache_path(config['discord']['trivia']['cache'])
        config['discord']['settings']['cache'] = self.update_cache_path(config['discord']['settings']['cache'])
        config['reddit']['cache'] = self.update_cache_path(config['reddit']['cache'])
        config['discord']['trivia']['stats_cache'] = self.update_cache_path(config['discord']['trivia']['stats_cache'])

        config['discord']['token'] = self.update_cache_path(config['discord']['token'])
        config['youtube']['token'] = self.update_cache_path(config['youtube']['token'])
        config['reddit']['token'] = self.update_cache_path(config['reddit']['token'])

        # retrieving the cache files, creating empyt ones if necessary
        self.scoreboard = self.get_cache(config['discord']['trivia']['cache'], 'Scoreboard Cache')
        self.settings = self.get_cache(config['discord']['settings']['cache'], 'Settings Cache')
        self.meme_cache = self.get_cache(config['reddit']['cache'], 'Reddit Cache')
        self.stats_cache = self.get_cache(config['discord']['trivia']['stats_cache'], 'Trivia Game Statistics')
        self.blocked = []
        self.busy_channels = []

        # retrieving tokens from files, exiting if invalid
        self.token = self.get_token(config['discord']['token'], 'Discord Token')[0].strip()
        self.yt_credentials = self.get_token(config['youtube']['token'], 'Youtube API Credentials')
        self.reddit_credentials = self.get_token(config['reddit']['token'], 'Reddit API Credentials')

        # setting intents
        intents = discord.Intents.default()
        #pylint:disable=assigning-non-slot
        intents.members = True

        # getting misc stuff from config
        self.color_list = list(c for c in self.config['discord']['colors'].values())
        self.start_time = datetime.now()

        # starting autosave
        asyncio.get_event_loop().create_task(self.auto_save())

        # calling the Base Constructor
        super().__init__(
            command_prefix=config['general']['prefix'],
            intents=intents,
            case_insensitive=True
        )

    async def auto_save(self):
        '''
        autosave feature
        '''
        self.logger.info('Autosave initialized.')
        while True:
            await asyncio.sleep(self.config['general']['autosave'])
            self.save_caches()
            self.logger.info(datetime.now().strftime('Autosave: %X on %a %d/%m/%y'))

    async def on_ready(self):
        if not self.started:
            self.logger.info('Logged in as: %s : %s', self.user.name, self.user.id)
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,name=random.choice(self.config['discord']['status'])))


    async def on_message(self, message):
        '''
        main function to recognize a bot command
        '''
        if message.author == self.user or message.author.id in self.blocked or message.author.bot:
            return
        channel = message.channel
        if not isinstance(channel, discord.channel.DMChannel):
            if not channel.permissions_for(channel.guild.me).send_messages:
                return

        await self.process_commands(message)

    def update_cache_path(self, path):
        '''
        preprends the cache directory to any given path
        '''
        return os.path.join(self.config['general']['cache_path'],path)

    def get_cache(self, path, name):
        '''
        loads cache located in the specified directory into memory,
        and creates an empty one if not valid.
        '''
        try:
            with open(path, 'rb') as cache_file:
                obj = pickle.load(cache_file)
                self.logger.info('successfully deserialized %s.',name)
                return obj
        except (FileNotFoundError, EOFError):
            self.logger.warning('could not deserialize %s! Ignoring.',name)
            open(path, 'wb').close()
            return {}

    def get_token(self, path, name):
        '''
        returns token from a given tokenfile location, and raises an error if not valid.
        '''
        try:
            with open(path, 'r', encoding='utf-8') as infofile:
                temp = infofile.readlines()
                if not temp:
                    raise EOFError
                return [x.strip() for x in temp]
        except (FileNotFoundError, EOFError) as token_error:
            self.logger.error('%s not found!',name)
            raise token_error

    def save_caches(self):
        with open(self.config['discord']['trivia']['cache'], 'wb') as sc_file:
            pickle.dump(self.scoreboard, sc_file)

        with open(self.config['reddit']['cache'], 'wb') as meme_file:
            pickle.dump(self.meme_cache, meme_file)

        with open(self.config['discord']['settings']['cache'], 'wb') as set_file:
            pickle.dump(self.settings, set_file)

        with open(self.config['discord']['trivia']['stats_cache'], 'wb') as stats_file:
            pickle.dump(self.stats_cache, stats_file)

        self.logger.debug('Successfully saved all cache files.')
