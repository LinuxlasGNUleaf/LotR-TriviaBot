# coding=utf-8

import asyncio
import logging
import os
import sys

import yaml

import discord_client

# ==========================> LOAD YAML FILE <==================================
with open("bot_config.yaml", 'r', encoding='utf-8') as cfg_stream:
    try:
        print('parsing config file...')
        config = yaml.safe_load(cfg_stream)
    except yaml.YAMLError as exc:
        print(f'While parsing the config file, the following error occurred:\n{exc}')
        sys.exit()
# ==============================================================================

if sys.platform not in config['filesystem']['bot_dir'].keys():
    print(f'\'{sys.platform}\' is not a supported platform. Add your system in the cache_dir field in config.yaml.')
    sys.exit(0)

# resolve directories and create missing ones
script_dir = os.path.dirname(os.path.realpath(__file__))
work_dir = os.path.expandvars(config['filesystem']['bot_dir'][sys.platform])
os.makedirs(work_dir, exist_ok=True)

# initialize logger
logfile = os.path.join(work_dir, config['logging']['logfile'])
print(f'logging events to: {logfile}')
logging.basicConfig(format='[%(asctime)s] [%(levelname)-8s] --- [%(module)-14s]: %(message)s',
                    level=logging.INFO,
                    handlers=[logging.FileHandler(logfile), logging.StreamHandler()])

# create bot
bot = discord_client.LotrBot(config, script_dir, work_dir)


async def main():
    await bot.start(None)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('keyboard interrupt detected, exiting.')
    bot.save_caches()
    logging.info('saved caches successfully.\n\n')
