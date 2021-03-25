
import pickle
import os
import sys
import logging
import random
import asyncio
#import platform
from time import strftime
import discord
from discord.ext import commands

class LotrBot(commands.Bot):
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

        # retrieving the cache files, creating empyt ones if necessary
        self.scoreboard = self.get_cache(config['discord']['trivia']['cache'], 'Scoreboard Cache')
        self.settings = self.get_cache(config['discord']['settings']['cache'], 'Settings Cache')
        self.meme_cache = self.get_cache(config['reddit']['cache'], 'Reddit Cache')
        self.stats_cache = self.get_cache(config['discord']['trivia']['stats_cache'], 'Trivia Game Statistics')
        self.blocked = []

        # retrieving tokens from files, exiting if invalid
        self.token = self.get_token(config['discord']['token'], 'Discord Token')[0].strip()
        self.yt_credentials = self.get_token(config['youtube']['token'], 'Youtube API Credentials')

        # setting intents
        intents = discord.Intents.default()
        intents.members = True

        # getting misc stuff from config
        self.color_list = [c for c in self.config['discord']['colors'].values()]

        # starting autosave
        asyncio.get_event_loop().create_task(self.auto_save())

        # calling the Base Constructor
        super().__init__(
            command_prefix=config['general']['prefix']+' ',
            intents=intents,
            case_insensitive=True
        )

    async def auto_save(self):
        '''
        autosave feature
        '''
        sys.stdout.write('\nAutosave initialized.')
        msg_len = 0
        while True:
            await asyncio.sleep(self.config['general']['autosave'])

            sc_file = open(self.config['discord']['trivia']['cache'], 'wb')
            pickle.dump(self.scoreboard, sc_file)
            sc_file.close()

            meme_file = open(self.config['reddit']['cache'], 'wb')
            pickle.dump(self.meme_cache, meme_file)
            meme_file.close()

            set_file = open(self.config['discord']['settings']['cache'], 'wb')
            pickle.dump(self.settings, set_file)
            set_file.close()

            msg = strftime('Last Autosave: %X on %a %d/%m/%y')
            msg_len = max(msg_len, len(msg))
            sys.stdout.write('\r{}{}'.format(msg, ((msg_len-len(msg))*' ')))


    async def on_ready(self):
        if not self.started:
            print(f"-----\nLogged in as: {self.user.name} : {self.user.id}\n-----\nMy current prefix is: {self.config['general']['prefix']}\n-----")
        else:
            print('[SYSTEM]: RESUME request probably failed. (Reconnected at {}.'.format(strftime('%X on %a %d/%m/%y)')))
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,name=random.choice(self.config['discord']['status'])))


    async def on_message(self, message):
        '''
        main function to recognize a bot command
        '''
        if message.author == self.user or message.author.id in self.blocked or message.author.bot:
            return
        channel = message.channel
        is_dm = isinstance(channel, discord.channel.DMChannel)
        if not is_dm:
            server = channel.guild
            if not channel.permissions_for(server.me).send_messages:
                return

        await self.process_commands(message)


    async def on_command_error(self, ctx, error):
        #Ignore these errors
        ignored = (commands.CommandNotFound, commands.UserInputError)
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.CommandOnCooldown):
            # If the command is currently on cooldown trip this
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            if int(h) == 0 and int(m) == 0:
                await ctx.send(f' You must wait {int(s)} seconds to use this command!')
            elif int(h) == 0 and int(m) != 0:
                await ctx.send(f' You must wait {int(m)} minutes and {int(s)} seconds to use this command!')
            else:
                await ctx.send(f' You must wait {int(h)} hours, {int(m)} minutes and {int(s)} seconds to use this command!')
        elif isinstance(error, commands.CheckFailure):
            # If the command has failed a check, trip this
            await ctx.send("Hey! You lack permission to use this command.")
        raise error

    def update_cache_path(self, path):
        return os.path.join(self.config['general']['cache_path'],path)
    
    def get_cache(self, path, name):
        '''
        loads cache located in the specified directory into memory,
        and creates an empty one if not valid.
        '''
        try:
            with open(path, 'rb') as cache_file:
                obj = pickle.load(cache_file)
                print('[INFO]: unserialized {}.'.format(name))
                return obj
        except (FileNotFoundError, EOFError):
            print('[WARN]: could not unserialize {}! Creating empty one instead.'.format(name))
            open(path, 'w').close()
            return {}


    def get_token(self, path, name):
        '''
        returns token from a given tokenfile location, and raises an error if not valid.
        '''
        try:
            with open(path, 'r') as infofile:
                temp = infofile.readlines()
                if not temp:
                    raise EOFError
                for i, item in enumerate(temp):
                    temp[i] = item.strip()
                return temp
        except (FileNotFoundError, EOFError) as token_error:
            msg = '[ERROR]: {} not found!'.format(name)
            raise EOFError(msg) from token_error