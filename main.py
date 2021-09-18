# coding=utf-8

import os
import sys
import logging
import yaml
import discord
import dc_client


# ==========================> LOAD YAML FILE <==================================
with open("config.yaml", 'r') as cfg_stream:
    try:
        print('parsing config file...')
        config = yaml.safe_load(cfg_stream)
    except yaml.YAMLError as exc:
        print(f'While parsing the config file, the following error occured:\n{exc}')
        sys.exit()

if sys.platform in config['general']['cache_path'].keys():
    config['general']['cache_path'] = os.path.expandvars(config['general']['cache_path'][sys.platform])
    os.makedirs(config['general']['cache_path'],exist_ok=True)
else:
    print(f'\'{sys.platform}\' is not a supported platform. Add your system in the cache_dir field in config.yaml.')
    exit(0)
# ==============================================================================
logfile = os.path.join(config['general']['cache_path'],config['general']['logfile'])
print(f'logging events to: {logfile}')

logging.basicConfig(format='[%(asctime)s] [%(levelname)-8s] --- [%(module)-11s]: %(message)s', level=logging.INFO, handlers=[logging.FileHandler(logfile), logging.StreamHandler()])

bot = dc_client.LotrBot(config)

if __name__ == '__main__':
    logging.info('--- Loading cogs...')
    for ext in os.listdir(os.path.join(os.getcwd(),'cogs')):
        try:
            if ext.endswith(".py") and not ext.startswith("_"):
                bot.load_extension(f"cogs.{ext[:-3]}")
        except discord.ext.commands.errors.ExtensionFailed as exc:
            logging.error('Unable to load %s extension. TRACEBACK:', ext)
            logging.exception(exc)
            logging.info('End of TRACEBACK.')

    bot.run(bot.token)
    bot.save_caches()
    logging.info('bot shutdown sequence complete.\n\n')
