# coding=utf-8

import os
import sys
import logging
import yaml

import dc_client

# ==========================> LOAD YAML FILE <==================================
with open("config.yaml", 'r') as cfg_stream:
    try:
        sys.stdout.write('parsing config file...')
        config = yaml.safe_load(cfg_stream)
        print('done.')
    except yaml.YAMLError as exc:
        print("While parsing the config file, the following error occured: "+exc)
        sys.exit()
# ==============================================================================

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)
bot = dc_client.LotrBot(config)

if __name__ == '__main__':
    for file in os.listdir(os.path.join(os.getcwd(),'cogs')):
        if file.endswith(".py") and not file.startswith("_"):
            bot.load_extension(f"cogs.{file[:-3]}")
    bot.run(bot.token)
