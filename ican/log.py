import logging
import sys
from . import __version__
from .emojis import rnd_good_emoji
from .emojis import rnd_bad_emoji


__all__ = [
    'logger',
    'DEBUG',
    'INFO',
    'WARNING',
    'ERROR'
]


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

    def __init__(self, fmt, style='%', emoji=True):
        super().__init__()
        self.fmt = fmt
        self.plain_fmt = '{message}'
        self.style = style
        self.FORMATS = {
            logging.DEBUG: self.GREEN + self.fmt + self.RESET,
            logging.INFO: self.INVERT + self.YELLOW + self.fmt + self.RESET,
            logging.WARNING: self.BLUE + self.plain_fmt + self.RESET,
            logging.ERROR: self.RED + self.fmt + self.RESET,
            logging.CRITICAL: self.INVERT + self.RED + self.fmt + self.RESET
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
        formatter = logging.Formatter(log_fmt, style=self.style)
        return formatter.format(record)


def setup_log_record_factory():
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        shorty = args[2].replace('.py','')
        file_lineno = f'{shorty}@{args[3]}'
        custom = list(args)
        custom[2] = file_lineno
        custom[3] = ''
        record = old_factory(*tuple(custom), **kwargs)
        record.custom_attribute = 0xdecafbad
        return record

    logging.setLogRecordFactory(record_factory)


def setup_console_handler(verbose, dry_run):
    if verbose:
        level = logging.DEBUG
    elif dry_run:
        level = logging.INFO
    else:
        level = logging.WARNING
    logger.__dry_run__ = False

    logger.setLevel(logging.DEBUG)
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(level)
    #format_str = '{filename:<20}{lineno}  {message}'
    format_str = '{filename:<16} {message}'
    formatter = CustomFormatter(format_str, style="{")
    console.setFormatter(formatter)
    logger.addHandler(console)

    logger.debug(f' ---===::: Welcome to ican v{__version__} :::===---')
    if dry_run:
            logger.__dry_run__ = True
            logger.info('--dry-run detected - no files will be modified')

def setup_file_handler(filename):
    format_str = '%(asctime)s | %(levelname)s | %(message)s'
    date_format = '%m-%d-%Y %H:%M:%S'
    formatter = logging.Formatter(format_str, date_format)
    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def ok_to_write():
    if not logger.__dry_run__:
        return True
    logger.info('Skipping file write @ --dry-run')
    return False


logger = logging.getLogger('ican')
#setup_log_record_factory()
