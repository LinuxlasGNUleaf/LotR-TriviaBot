# coding=utf-8

import os
import sys
import logging
import yaml
import asyncio
import dc_client

import backend_utils as bu

# ==========================> LOAD YAML FILE <==================================
with open("config.yaml", 'r', encoding='utf-8') as cfg_stream:
    try:
        print('parsing config file...')
        config = yaml.safe_load(cfg_stream)
    except yaml.YAMLError as exc:
        print(f'While parsing the config file, the following error occured:\n{exc}')
        sys.exit()
# ==============================================================================

if sys.platform not in config['backend']['bot_dir'].keys():
    print(f'\'{sys.platform}\' is not a supported platform. Add your system in the cache_dir field in config.yaml.')
    sys.exit(0)

# resolve directories and create missing ones
script_dir = os.path.dirname(os.path.realpath(__file__))
work_dir = os.path.expandvars(config['backend']['bot_dir'][sys.platform])
os.makedirs(work_dir, exist_ok=True)

# initialize logger
logfile = os.path.join(work_dir, config['backend']['logfile'])
print(f'logging events to: {logfile}')
logging.basicConfig(format='[%(asctime)s] [%(levelname)-8s] --- [%(module)-11s]: %(message)s',
                    level=logging.INFO,
                    handlers=[logging.FileHandler(logfile), logging.StreamHandler()])

# create bot
bot = dc_client.LotrBot(config, script_dir, work_dir)


async def main():
    await bot.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('keyboard interrupt detected, exiting.')
    bot.save_caches()
    logging.info('saved caches successfully.\n\n')
