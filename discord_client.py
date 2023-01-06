import asyncio
import logging
import os
from datetime import datetime

import discord
import yaml
from discord.ext import commands, tasks

import backend_utils as bu


class LotrBot(commands.Bot):
    """
    The LotR-Bot. Subclass of discord.ext.commands.Bot
    """

    def __init__(self, config, script_dir, work_dir):
        self.logger = logging.getLogger(__name__)

        self.script_dir = script_dir
        self.cog_dir = os.path.join(script_dir, *config['filesystem']['cog_dir'])
        self.cog_prefix = '.'.join(config['filesystem']['cog_dir']) + '.'

        self.work_dir = work_dir
        self.script_dir = script_dir
        self.token_dir = os.path.join(work_dir, config['filesystem']['token_dir'])
        self.cache_dir = os.path.join(work_dir, config['filesystem']['cache_dir'])
        os.makedirs(self.token_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

        self.running_cogs = []
        self.save_functions = {}

        self.options = config
        self.tokens, self.caches, self.caches_locations, self.assets = self.load_files_for_context(self.options,
                                                                                                   'LotrBot')
        self.start_time = 0

        self.blocked_users = []
        self.busy_channels = []

        # setting intents
        intents = discord.Intents.all()

        # calling the Superclass-Constructor
        super().__init__(
            command_prefix=config['discord']['prefix'],
            intents=intents,
            case_insensitive=True
        )

    async def start(self, _, *, reconnect: bool = True):
        # load cogs
        await self.load_cogs()

        # adjust task intervals and start
        self.autosave.change_interval(minutes=self.options['discord']['autosave'])
        self.autosave.start()

        # save startup time
        self.start_time = datetime.now()

        # establish connection
        await super().start(token=self.tokens['discord'][0], reconnect=reconnect)

    async def load_cogs(self, cog_list=None):
        cog_list = cog_list if cog_list else self.get_fs_cogs()
        status = {x: '' for x in cog_list}
        with bu.LogManager(self.logger, logging.INFO, 'cog loading', self.options['logging']['log_width']):
            for cog in cog_list:
                cog_name = cog.split('.')[-1].upper()
                try:
                    logging.info(f'attempting to load {cog_name}...')
                    await self.load_extension(cog)
                    self.running_cogs.append(cog)
                except commands.ExtensionFailed as exc:
                    logging.error(f'{cog_name} failed with the following exception:')
                    with bu.LogManager(self.logger, logging.ERROR, 'EXCEPTION',
                                       self.options['logging']['log_width']):
                        logging.exception(exc)
        return status

    async def unload_cogs(self, cog_list):
        status = {x: '' for x in cog_list}
        with bu.LogManager(self.logger, logging.INFO, 'cog unloading', self.options['logging']['log_width']):
            for cog in cog_list:
                cog_name = cog.split('.')[-1].upper()
                try:
                    if cog in self.running_cogs:
                        self.running_cogs.remove(cog)
                    logging.info(f'attempting to unload {cog_name}...')
                    await self.unload_extension(cog)
                    status[cog] = 'OK'
                except commands.ExtensionNotFound:
                    logging.error(f'{cog_name} could not be found in this package and will be skipped.')
                    status[cog] = 'N/A'
                except commands.ExtensionNotLoaded:
                    logging.error(f'{cog} was not loaded and will be skipped.')
                    status[cog] = 'N/A'
        return status

    async def reload_cogs(self, cog_list=None):
        self.logger.info(f'active cogs: {self.running_cogs}')
        self.logger.info(f'filesystem cogs: {self.get_fs_cogs()}')
        unload_list = cog_list if cog_list else self.running_cogs.copy()
        load_list = cog_list if cog_list else self.get_fs_cogs().copy()
        await self.unload_cogs(unload_list)
        load_status = await self.load_cogs(load_list)
        status = {}
        for cog in set(unload_list + load_list):
            if cog in unload_list and load_list:
                status[cog] = load_status[cog]
            elif cog in load_list:
                status[cog] = 'NEW'
            else:
                status[cog] = 'N/A'
        return status

    def load_config_for_cog(self, cog):
        with open(self.get_config_location(cog), 'r', encoding='utf-8') as cfg_stream:
            try:
                self.logger.info(f'parsing config file for {cog.upper()}...')
                return yaml.safe_load(cfg_stream)
            except yaml.YAMLError as exc:
                self.logger.info(f'while parsing the config file, the following error occurred:')
                raise exc

    def load_files_for_context(self, config, name):
        tokens, caches, caches_locations, assets = {}, {}, {}, {}

        if config['tokens']:
            self.logger.info(f'loading tokens for {name.upper()}...')
            # load tokens
            for token, token_file in config['tokens'].items():
                token_name = token_file
                token_file = os.path.join(self.token_dir, token_file)
                tokens[token] = bu.load_token(token_file, token_name, self.logger)

        if config['caches']:
            self.logger.info(f'loading caches for {name.upper()}...')
            # load caches
            for cache, cache_file in config['caches'].items():
                cname = cache_file
                cache_file = os.path.join(self.cache_dir, cache_file)
                caches[cache] = bu.load_cache(cache_file, cname, self.logger)
                caches_locations[cache] = cache_file

        if config['assets']:
            self.logger.info(f'resolving assets for {name.upper()}...')
            # resolve asset names
            for asset, asset_file in config['assets'].items():
                assets[asset] = self.get_asset_location(asset_file)

        return tokens, caches, caches_locations, assets

    @tasks.loop()
    async def autosave(self):
        self.save_caches()
        self.logger.debug(datetime.now().strftime('Autosave: %X on %a %d/%m/%y'))

    @autosave.before_loop
    async def before_autosave(self):
        self.logger.info(f'autosave is ready and will start in {int(self.autosave.minutes)} minutes.')
        await asyncio.sleep(self.autosave.minutes * 60)

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

    def save_caches(self):
        # save caches for bot itself
        bu.save_caches(self.caches, self.caches_locations, self.logger, 'LotrBot')
        # save caches of all registered cogs
        for save_func in self.save_functions.values():
            save_func()
        self.logger.debug('successfully saved all caches.')

    def get_fs_cogs(self):
        return [self.cog_prefix + str(cog)[:-3].lower() for cog in os.listdir(self.cog_dir) if
                str(cog).endswith(".py") and not str(cog).startswith("_")]

    def get_asset_location(self, name):
        return os.path.join(self.script_dir, self.options['filesystem']['asset_dir'],
                            name)

    def get_config_location(self, name):
        return os.path.join(self.script_dir, self.options['filesystem']['config_dir'],
                            f'{name.lower()}.yaml')
