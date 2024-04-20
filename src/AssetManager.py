import logging
import os.path

import yaml


class AssetManager:
    def __init__(self, bot_config):
        self.bot_config = bot_config
        self.config = bot_config['asset_manager']
        self.logger = logging.getLogger(__name__)
        self.logger.level = logging.INFO

        self.token_dir = os.path.expandvars(self.config['token_dir'])
        self.asset_dir = os.path.join(self.bot_config['root_dir'], self.config['asset_dir'])
        self.cog_dir = os.path.join(self.bot_config['root_dir'], self.config['cog_dir'])
        self.cog_prefix = os.path.relpath(self.cog_dir, self.bot_config['root_dir']).replace('/', '.') + '.'
        self.config_dir = os.path.join(self.bot_config['root_dir'], self.config['config_dir'])

    def load_config_for_cog(self, cog_name: str):
        with open(os.path.join(self.config_dir, f'{cog_name}.yaml'), 'r', encoding='utf-8') as config_stream:
            try:
                self.logger.info(f'Parsing config file for {cog_name.upper()}')
                return yaml.safe_load(config_stream)
            except yaml.YAMLError as exc:
                self.logger.info(f'While parsing the config file, the following error occurred:')
                raise exc

    def load_assets(self, working_config):
        if 'assets' not in working_config or not working_config['assets']:
            return {}
        return {name: os.path.join(self.asset_dir, file) for name, file in working_config['assets'].items()}

    def load_tokens(self):
        tokens = {}
        for token in os.listdir(self.token_dir):
            with open(os.path.join(self.token_dir, token), 'r', encoding='utf-8') as token_file:
                tokens[os.path.splitext(token)[0]] = token_file.read().strip()
        return tokens

    def get_existing_cogs(self):
        cogs = {}
        for cog in os.listdir(self.cog_dir):
            cog_filename, cog_ext = os.path.splitext(cog)
            if cog_ext.lower() != '.py' or cog_filename.startswith('_'):
                continue
            cogs[cog_filename] = self.cog_prefix + cog_filename
        return cogs
