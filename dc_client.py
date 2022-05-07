import os
import logging
import random
import asyncio
from datetime import datetime
import discord
from discord.ext import commands, tasks

import backend_utils as bu


class LotrBot(commands.Bot):
    """
    The LotR-Bot. Subclass of discord.ext.commands.Bot
    """

    def __init__(self, config, script_dir, work_dir):
        self.started = False
        self.logger = logging.getLogger(__name__)

        self.script_dir = script_dir
        self.cog_dir = os.path.join(script_dir, *config['backend']['cog_dir'])
        self.cog_prefix = '.'.join(config['backend']['cog_dir']) + '.'

        self.work_dir = work_dir
        self.script_dir = script_dir
        self.token_dir = os.path.join(work_dir, config['backend']['token_dir'])
        self.cache_dir = os.path.join(work_dir, config['backend']['cache_dir'])
        os.makedirs(self.token_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

        self.config = config
        self.caches = {}
        self.tokens = {}
        self.start_time = 0

        # load tokens
        with bu.LogManager(self.logger, logging.INFO, 'token loading', self.config['backend']['log_width']):
            for token, token_file in self.config['backend']['tokens'].items():
                token_name = token_file
                token_file = os.path.join(self.token_dir, token_file)
                self.tokens[token] = bu.load_token(token_file, token_name)

        # load caches
        with bu.LogManager(self.logger, logging.INFO, 'cache loading', self.config['backend']['log_width']):
            for cache, cache_file in self.config['backend']['caches'].items():
                cname = cache_file
                cache_file = os.path.join(self.cache_dir, cache_file)
                self.caches[cache] = bu.load_cache(cache_file, cname)

        self.blocked_users = []
        self.busy_channels = []
        self.colors = config['discord']['colors']

        # setting intents
        intents = discord.Intents.all()

        # calling the Superclass-Constructor
        super().__init__(
            command_prefix=config['discord']['prefix'],
            intents=intents,
            case_insensitive=True,
            activity=self.get_random_presence()
        )

    async def on_ready(self):
        if not self.started:
            self.logger.info('Logged in as: %s : %s', self.user.name, self.user.id)

    async def start(self, *, reconnect: bool = True):
        # load cogs
        await self.load_cogs()

        # adjust task intervals
        self.autosave.change_interval(minutes=self.config['backend']['autosave'])
        self.autopresence.change_interval(minutes=self.config['discord']['autopresence'])

        # start tasks
        self.autosave.start()
        self.autopresence.start()

        # save startup time
        self.start_time = datetime.now()

        # start connection
        await super().start(token=self.tokens['discord'][0], reconnect=reconnect)

    async def load_cogs(self, cog_list=None):
        cog_list = cog_list if cog_list else self.get_all_cogs()
        status = {x: '' for x in cog_list}
        with bu.LogManager(self.logger, logging.INFO, 'cog loading', self.config['backend']['log_width']):
            for cog in cog_list:
                try:
                    logging.info(f'Attempting to load {cog}...')
                    await self.load_extension(cog)
                except commands.ExtensionFailed as exc:
                    logging.error(f'{cog} failed with the following exception:')
                    with bu.LogManager(self.logger, logging.ERROR, 'EXCEPTION',
                                       self.config['backend']['log_width']):
                        logging.exception(exc)
        return status

    async def unload_cogs(self, cog_list=None):
        cog_list = cog_list if cog_list else self.get_all_cogs()
        status = {x: '' for x in cog_list}
        with bu.LogManager(self.logger, logging.INFO, 'cog unloading', self.config['backend']['log_width']):
            for cog in cog_list:
                try:
                    logging.info(f'Attempting to unload {cog}...')
                    await self.unload_extension(cog)
                except commands.ExtensionNotFound:
                    logging.error(f'{cog} could not be found in this package and will be skipped.')
                    status[cog] = 'N/A'
                except commands.ExtensionNotLoaded:
                    logging.error(f'{cog} was not loaded and will be skipped.')
        return status

    async def reload_cogs(self, cog_list=None):
        print(f'Active cogs: {self.get_active_cogs()}')
        print(f'All cogs: {self.get_all_cogs()}')
        cog_list = cog_list if cog_list else set(self.get_active_cogs() + self.get_all_cogs())
        status = {x: '' for x in cog_list}
        with bu.LogManager(self.logger, logging.INFO, 'cog reloading', self.config['backend']['log_width']):
            for cog in cog_list:
                logging.info(f'Attempting to reload {cog} ...')
                try:
                    await self.unload_extension(cog)
                    await self.load_extension(cog)
                    status[cog] = 'OK'
                except commands.ExtensionNotFound:
                    logging.warning(f'{cog} could not be found and will be skipped.')
                    status[cog] = 'N/A'
                except (commands.ExtensionFailed, commands.NoEntryPointError) as exc:
                    logging.error(f'{cog} failed with the following exception:')
                    with bu.LogManager(self.logger, logging.ERROR, 'EXCEPTION',
                                       self.config['backend']['log_width']):
                        logging.exception(exc)
                    status[cog] = "FAIL"
                except commands.ExtensionNotLoaded:
                    logging.info(f'{cog} was not loaded before and will be loaded instead of reloaded.')
                    await self.load_cogs([cog])
                    status[cog] = "NEW"

        return status

    @tasks.loop()
    async def autosave(self):
        bu.save_caches(self.config, self.caches, self.cache_dir)
        self.logger.info(datetime.now().strftime('Autosave: %X on %a %d/%m/%y'))

    @autosave.before_loop
    async def before_autosave(self):
        self.logger.info(f'Autosave is ready and will start in {int(self.autosave.minutes)} minutes.')
        await asyncio.sleep(self.autosave.minutes * 60)

    @tasks.loop()
    async def autopresence(self):
        new_activity = self.get_random_presence()
        self.logger.info(f'Changing presence to: "Watching {new_activity.name}"')
        await self.change_presence(activity=new_activity)

    @autopresence.before_loop
    async def before_autopresence(self):
        self.logger.info('Waiting for the bot to finish startup before changing presence...')
        await self.wait_until_ready()
        self.logger.info(f'Startup complete, presence will be updated in {int(self.autopresence.minutes)} minutes.')
        await asyncio.sleep(self.autopresence.minutes * 60)

    async def on_message(self, message):
        """
        main function to recognize a bot command
        """
        if message.author == self.user or message.author.id in self.blocked_users or message.author.bot:
            return
        channel = message.channel
        if not isinstance(channel, discord.channel.DMChannel):
            if not channel.permissions_for(channel.guild.me).send_messages:
                return
        await self.process_commands(message)

    def get_random_presence(self):
        return discord.Activity(type=discord.ActivityType.watching,
                                name=random.choice(self.config['discord']['status']))

    def get_all_cogs(self):
        return [self.cog_prefix + cog[:-3].lower() for cog in os.listdir(self.cog_dir) if
                cog.endswith(".py") and not cog.startswith("_")]

    def get_active_cogs(self):
        return [self.cog_prefix + cog.lower() for cog in self.cogs.keys()]

    def get_asset_name(self, name):
        return os.path.join(self.script_dir, self.config['backend']['asset_dir'], self.config['backend']['assets'][name])
