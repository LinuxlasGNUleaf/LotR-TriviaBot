import logging
import os
import yaml

from src.LotrBot import LotrBot

# initialize logger
logging.basicConfig(format='[%(asctime)s] [%(levelname)-8s] --- [%(module)-14s]: %(message)s',
                    level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.level = logging.INFO

# load config file
with open("config/MAIN_CONFIG.yaml", 'r', encoding='utf-8') as cfg_stream:
    try:
        logger.info('parsing config file...')
        config = yaml.safe_load(cfg_stream)
    except yaml.YAMLError as exc:
        logger.error(f'While parsing the config file, the following error occurred:')
        logger.exception(exc)
        raise exc

root_dir = os.path.expandvars(config['root_dir'])

if __name__ == '__main__':
    bot = LotrBot(config=config)
    bot.startup()
