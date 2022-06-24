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

def set_logger_level(verbose, dry_run):
    if verbose:
        logger.setLevel(logging.DEBUG)
    elif dry_run:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)


class CustomFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""
    
    BLACK = '\u001b[30;1m'
    RED = '\u001b[31;1m'
    GREEN = '\u001b[32;1m'
    YELLOW = '\u001b[33;1m'
    BLUE = '\u001b[34;7m'
    MAGENTA = '\u001b[35;1m'
    CYAN = '\u001b[36;1m'
    WHITE = '\u001b[37;1m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    INVERT = '\033[7m'
    RESET = '\u001b[0m'

    def __init__(self, fmt, emoji=True):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.GREEN + self.fmt + self.RESET,
            logging.INFO: self.INVERT + self.YELLOW + self.fmt + self.RESET,
            logging.WARNING: self.BLUE + self.fmt + self.RESET,
            logging.ERROR: self.RED + self.fmt + self.RESET,
            logging.CRITICAL: self.INVERT + self.RED +\
                self.fmt + self.RESET
        }
        if emoji:
            warning = self.FORMATS[logging.WARNING]
            self.FORMATS[logging.WARNING] = rnd_good_emoji(2) +\
                "  " + warning + "  " + rnd_good_emoji(2)

            error = self.FORMATS[logging.ERROR]
            self.FORMATS[logging.ERROR] = rnd_bad_emoji(2) +\
                "  " + error + "  " + rnd_bad_emoji(2)

            critical = self.FORMATS[logging.CRITICAL]
            self.FORMATS[logging.CRITICAL] = rnd_bad_emoji(3) +\
                "  " + critical + "  " + rnd_bad_emoji(3)


    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger('ican')
console = logging.StreamHandler()
format_str = '%(message)s'
console.setFormatter(CustomFormatter(format_str))
logger.addHandler(console)