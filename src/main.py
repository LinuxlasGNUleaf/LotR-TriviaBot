import logging
import os
import yaml

from LotrBot import LotrBot

# initialize logger
logging.basicConfig(format='[%(asctime)s] [%(levelname)-8s] --- [%(module)-14s]: %(message)s',
                    level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.level = logging.INFO

# load config file
with open("./config/config.yaml", 'r', encoding='utf-8') as cfg_stream:
    try:
        logger.info('parsing config file...')
        config = yaml.safe_load(cfg_stream)
    except yaml.YAMLError as exc:
        logger.error(f'While parsing the config file, the following error occurred:')
        logger.exception(exc)
        raise exc

root_dir = os.path.expandvars(config['root_dir'])
subdirs = {name: os.path.join(root_dir, path) for name, path in config['subdirs'].items()}

token_dir = os.path.expandvars(config['token_dir'])
tokens = {}
for token in os.listdir(token_dir):
    with open(os.path.join(token_dir, token), 'r', encoding='utf8') as token_file:
        tokens[os.path.splitext(token)[0]] = token_file.read().strip()


if __name__ == '__main__':
    bot = LotrBot(config=config, tokens=tokens)
    bot.startup()
