import logging
from .emojis import rnd_good_emoji
from .emojis import rnd_bad_emoji


__all__ = [
    'logger',
    'DEBUG',
    'INFO',
    'WARNING',
    'ERROR'
]

def set_logger_level(verbose):
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)


class CustomFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""
    
    BLACK = '\u001b[30;1m'
    RED = '\u001b[31;1m'
    GREEN = '\u001b[32;1m'
    YELLOW = '\u001b[33;1m'
    BLUE = '\u001b[34;1m'
    MAGENTA = '\u001b[35;1m'
    CYAN = '\u001b[36;1m'
    WHITE = '\u001b[37;1m'
    RESET = '\u001b[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.GREEN + self.fmt + self.RESET,
            logging.INFO: self.UNDERLINE + self.YELLOW + self.fmt + self.RESET,
            logging.WARNING: self.BLUE + self.fmt + self.RESET,
            logging.ERROR: self.MAGENTA + self.fmt + self.RESET,
            logging.CRITICAL: self.UNDERLINE + self.RED +\
                self.fmt + self.RESET
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger('ican')
console = logging.StreamHandler()
format_str = '%(message)s'
console.setFormatter(CustomFormatter(format_str))
logger.addHandler(console)