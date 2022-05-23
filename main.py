# coding=utf-8

import os
import sys
import logging
import yaml
import asyncio
import dc_client

# ==========================> LOAD YAML FILE <==================================
with open("config.yaml", 'r', encoding='utf-8') as cfg_stream:
    try:
        print('parsing config file...')
        config = yaml.safe_load(cfg_stream)
    except yaml.YAMLError as exc:
        print(f'While parsing the config file, the following error occured:\n{exc}')
        sys.exit()

if sys.platform in config['backend']['bot_dir'].keys():
    work_dir = config['backend']['bot_dir']
    work_dir = os.path.expandvars(work_dir[sys.platform])
    os.makedirs(work_dir, exist_ok=True)
else:
    print(f'\'{sys.platform}\' is not a supported platform. Add your system in the cache_dir field in config.yaml.')
    sys.exit(0)
# ==============================================================================

logfile = os.path.join(work_dir, config['backend']['caches']['logfile'])
print(f'logging events to: {logfile}')

logging.basicConfig(format='[%(asctime)s] [%(levelname)-8s] --- [%(module)-11s]: %(message)s',
                    level=logging.INFO,
                    handlers=[logging.FileHandler(logfile), logging.StreamHandler()])

script_dir = os.path.dirname(os.path.realpath(__file__))
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