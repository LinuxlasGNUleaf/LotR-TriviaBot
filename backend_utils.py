"""
frequently used utils for the backend of the bot
"""

import os
import pickle

import yaml


def bool_emoji(val):
    return '✅' if val else '❌'


def ordinal(n):
    """
    Convert an integer into its ordinal representation::

        make_ordinal(0)   => '0th'
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'
    """
    n = int(n)
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix


def genitive(word):
    word = word.strip()
    return f"{word}'" if word.endswith('s') else f"{word}'s"


def map_values(val: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """
    maps a value in a range to another range
    """
    val = min(max(val, in_min), in_max)
    return (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def load_cache(path, name, logger):
    """
    Loads a human-readable YAML cache and migrates the former pickle format
    when it is encountered for the first time.
    """
    legacy_path = os.path.splitext(path)[0] + '.cache'

    try:
        with open(path, 'r', encoding='utf-8') as cache_file:
            obj = yaml.safe_load(cache_file)
            logger.info(f'successfully loaded "{name}"')
            return {} if obj is None else obj
    except FileNotFoundError:
        pass
    except yaml.YAMLError:
        logger.exception(f'could not parse cache "{name}"')
        return {}

    try:
        with open(legacy_path, 'rb') as cache_file:
            obj = pickle.load(cache_file)
        logger.info(f'migrating legacy cache "{name}" to YAML')
        _save_cache(path, obj)
        return obj
    except FileNotFoundError:
        logger.warning(f'could not load "{name}"! creating an empty cache.')
        _save_cache(path, {})
        return {}
    except (EOFError, pickle.UnpicklingError):
        logger.exception(f'could not migrate legacy cache "{name}"')
        return {}


def load_token(path, name, logger):
    """
    returns token from a given token location, and raises an error if not valid.
    """
    try:
        with open(path, 'r', encoding='utf-8') as info_file:
            temp = info_file.readlines()
            if not temp:
                raise EOFError
            logger.info(f'successfully read "{name}"')
            return [x.strip() for x in temp]
    except (FileNotFoundError, EOFError) as token_error:
        logger.fatal(f'token "{name}" not found!')
        raise token_error


def save_caches(caches, caches_locations, logger, cog_name):
    for cache, cache_path in caches_locations.items():
        _save_cache(cache_path, caches[cache])
    logger.debug(f'successfully saved all caches for {cog_name}.')


def _save_cache(path, value):
    with open(path, 'w', encoding='utf-8') as cache_file:
        yaml.safe_dump(value, cache_file, allow_unicode=True, sort_keys=False)


class LogManager:
    def __init__(self, logger, level, title, width):
        self.logger = logger
        self.level = level
        self.title = title.upper()
        self.width = width

    def __enter__(self):
        self.logger.log(self.level, f'> START OF {self.title} <'.center(self.width, '='))

    def __exit__(self, *args):
        self.logger.log(self.level, f'> END OF {self.title} <'.center(self.width, '='))
