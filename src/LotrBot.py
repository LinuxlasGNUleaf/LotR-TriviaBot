import asyncio
import logging
import signal

import discord
from discord.ext import commands

from src.AssetManager import AssetManager
from src.DataManager import DataManager


class LotrBot(commands.Bot):
    def __init__(self, config):
        self.data_mgr = DataManager(bot_config=config)
        self.data_mgr.setup_cog(cog_name='bot', working_config=config)

        self.asset_mgr = AssetManager(bot_config=config)

        self.tasks: list[asyncio.Task] = []
        self.config: dict = config
        self.tokens: dict = self.asset_mgr.load_tokens()
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.level = logging.INFO

        super().__init__(command_prefix="lotr ", intents=discord.Intents.all())

    def startup(self):
        try:
            asyncio.run(self.run_tasks())
        except KeyboardInterrupt:
            for task in self.tasks:
                task.cancel()

    async def run_tasks(self):
        # SIGTERM handler
        try:
            self.logger.info('Registering SIGTERM handler')
            asyncio.get_event_loop().add_signal_handler(signal.SIGTERM, self.handle_sigterm)
        except NotImplementedError:
            self.logger.warning('SIGTERM handler could not be registered, since your system does not support it')

        self.tasks = []
        self.tasks.append(asyncio.create_task(super().start(token=self.tokens['discord_token'])))

        self.logger.info('Running all configured tasks')
        try:
            # gather all tasks
            await asyncio.gather(*self.tasks)

        except asyncio.CancelledError:
            self.logger.info('Received SIGINT, trying graceful shutdown')
            self.shutdown()

    def handle_sigterm(self):
        self.logger.info('Received SIGTERM, trying graceful shutdown')
        self.shutdown()

    def shutdown(self):
        self.data_mgr.disconnect()
        for task in self.tasks:
            task.cancel()
        self.logger.info('Shutdown complete, goodbye.')

    async def on_ready(self):
        await self.load_cogs()
        try:
            synced = await self.tree.sync()
            self.logger.info(f'Synced {len(synced)} command(s).')
        except Exception as e:
            self.logger.error('Sync failed with this exception:')
            raise e

    async def load_cogs(self):
        for cog_name, cog_qualifier in self.asset_mgr.get_existing_cogs().items():
            try:
                self.logger.info(f'//====> now loading \'{cog_name}\'')
                await self.load_extension(cog_qualifier)
                self.logger.info(f'\\\\====> load done for \'{cog_name}\'')
            except commands.ExtensionFailed as exc:
                self.logger.error(f'{cog_name} failed with the following exception:')
                self.logger.exception(exc)
