import logging
import os.path

import yaml


class AssetManager:
    def __init__(self, bot_config):
        self.bot_config = bot_config
        self.config = bot_config['asset_manager']
        self.logger = logging.getLogger(__name__)
        self.logger.level = logging.INFO

    def load_config_for_cog(self, cog_name: str):
        path = os.path.join(self.bot_config['root_dir'],
                            self.config['config_dir'],
                            cog_name.lower())

        with open(path, 'r', encoding='utf-8') as config_stream:
            try:
                self.logger.info(f'parsing config file for {cog_name.upper()}...')
                return yaml.safe_load(config_stream)
            except yaml.YAMLError as exc:
                self.logger.info(f'while parsing the config file, the following error occurred:')
                raise exc

    def load_assets(self, working_config):
        assets = {}
        for asset_name, asset_file in working_config['assets'].items():
            path = os.path.join(self.bot_config['root_dir'],
                                self.config['asset_dir'],
                                asset_file)
            assets[asset_name] = path
        return assets

    def load_tokens(self):
        token_dir = os.path.expandvars(self.config['token_dir'])
        tokens = {}
        for token in os.listdir(token_dir):
            self.logger.info(f'loading secret file \'{token}\'')
            with open(os.path.join(token_dir, token), 'r', encoding='utf-8') as token_file:
                tokens[os.path.splitext(token)[0]] = token_file.read().strip()
        return tokens
