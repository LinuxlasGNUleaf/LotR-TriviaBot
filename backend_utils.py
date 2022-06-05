"""
frequently used utils for the backend of the bot
"""

import pickle


def ordinal(n):
    return f'{n}{"tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4]}'


def map_values(val, in_min, in_max, out_min, out_max):
    """
    maps a value in a range to another range
    """
    val = min(max(val, in_min), in_max)
    return (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def load_cache(path, name, logger):
    """
    loads cache located in the specified directory into memory,
    and creates an empty one if not valid.
    """
    try:
        with open(path, 'rb') as cache_file:
            obj = pickle.load(cache_file)
            logger.info(f'successfully deserialized "{name}"')
            return obj
    except (FileNotFoundError, EOFError):
        logger.warning(f'could not deserialize "{name}"! creating empty cache.')
        open(path, 'wb').close()
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
        with open(cache_path, 'wb') as cache_file:
            pickle.dump(caches[cache], cache_file)
    logger.debug(f'successfully serialized all caches for {cog_name}.')


class LogManager:
    def __init__(self, logger, level, title, width):
        self.logger = logger
        self.level = level
        self.title = title.upper()
        self.width = width

    def __enter__(self):
        print()
        self.logger.log(self.level, f'> START OF {self.title} <'.center(self.width, '='))

    def __exit__(self, *args):
        self.logger.log(self.level, f'> END OF {self.title} <'.center(self.width, '='))
        print()
