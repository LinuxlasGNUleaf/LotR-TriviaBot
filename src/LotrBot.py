import asyncio
import logging
import signal

import discord
from discord.ext import commands
from discord import app_commands


class LotrBot(commands.Bot):
    def __init__(self, config, tokens):
        self.tasks: list[asyncio.Task] = []
        self.config: dict = config
        self.tokens: dict = tokens
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
            # TODO: close DB connections
            pass

    def handle_sigterm(self):
        self.logger.info('Received SIGTERM, trying graceful shutdown')
        for task in self.tasks:
            task.cancel()
        self.logger.info('Shutdown complete, goodbye.')

    async def on_ready(self):
        self.logger.info('Bot is ready!')
        try:
            synced = await self.tree.sync()
            self.logger.info(f'Synced {len(synced)} command(s).')
        except Exception as e:
            self.logger.error('Sync failed with this exception:')
            raise e
