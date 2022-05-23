"""
frequently used utils for the backend of the bot
"""


def ordinal(n):
    return f'{n}{"tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4]}'


def map_vals(val, in_min, in_max, out_min, out_max):
    """
    maps a value in a range to another range
    """
    val = min(max(val, in_min), in_max)
    return (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


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
