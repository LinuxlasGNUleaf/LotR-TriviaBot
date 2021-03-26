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
# ==============================================================================
logfile = os.path.join(os.path.expandvars(config['general']['cache_path']),config['general']['logfile'])
print(f'logging events to: {logfile}')

logging.basicConfig(format='[%(asctime)s] [%(levelname)-8s] --- [%(module)-10s]: %(message)s', level=logging.INFO, handlers=[logging.FileHandler(logfile), logging.StreamHandler()])

bot = dc_client.LotrBot(config)

if __name__ == '__main__':
    logging.info('--- Loading cogs...')
    for ext in os.listdir(os.path.join(os.getcwd(),'cogs')):
        try:
            if ext.endswith(".py") and not ext.startswith("_"):
                bot.load_extension(f"cogs.{ext[:-3]}")
        except discord.ext.commands.errors.ExtensionFailed as exc:
            logging.error('Unable to load extension %s... ignoring.', ext)
    try:
        bot.run(bot.token)
    except Exception as exc:
        logging.warning('Bot exited with error, ignoring.')
        bot.saveCaches()
        raise exc
    bot.saveCaches()
    logging.info('bot shutdown sequence complete.\n\n')
