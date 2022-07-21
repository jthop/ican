# -*- coding: utf-8 -*-

import logging
import sys

# debug=10, info=20, warning=30, error=40, critical=50


class IcanFormatter(logging.Formatter):
    """colors from https://stackoverflow.com/a/56944256/3638629"""

    BLACK = "\u001b[30;1m"
    RED = "\u001b[31;1m"
    GREEN = "\u001b[32;1m"
    YELLOW = "\u001b[33;1m"
    BLUE = "\u001b[34;7m"
    MAGENTA = "\u001b[35;1m"
    CYAN = "\u001b[36;1m"
    WHITE = "\u001b[37;1m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    INVERT = "\033[7m"
    RESET = "\u001b[0m"

    DEFAULT_FORMAT = "%(filename)-12s  %(message)s"

    def __init__(self, fmt=DEFAULT_FORMAT, emoji=True):
        super().__init__()
        self.fmt = fmt
        self.plain = "%(message)s"
        self.FORMATS = {}
        self.FORMATS[logging.DEBUG] = self.color(self.MAGENTA)
        self.FORMATS[IcanLogger.VERBOSE] = self.color(self.YELLOW)
        self.FORMATS[IcanLogger.DRY_RUN] = self.color(self.BOLD + self.BLUE)
        self.FORMATS[logging.INFO] = self.color(self.BOLD + self.GREEN, True)
        self.FORMATS[logging.WARNING] = self.color(self.RED)
        self.FORMATS[logging.ERROR] = self.color(self.RED)
        self.FORMATS[logging.CRITICAL] = self.color(self.INVERT + self.RED)

        if emoji:
            pass

    def color(self, format, plain=False):
        if plain:
            return format + self.plain + self.RESET
        return format + self.fmt + self.RESET

    def format(self, record):
        """Use the FORMATS dict to apply color, also we strip
        .py from the record.filename.
        """

        record.filename = record.filename.replace(".py", "").upper()
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class IcanLogger(logging.getLoggerClass()):
    """
    assert logging.getLevelName(VERBOSE) == 'VERBOSE'
    assert logging.getLevelName(DRY_RUN) == 'DRY_RUN'
    """

    VERBOSE = 11  # like debug, print on console and file
    DRY_RUN = 15  # dry_run related messages
    DEFAULT_FILEHANDLER = "%(asctime)s | %(levelname)s | %(message)s"

    def __init__(self, name, level=logging.DEBUG):
        super().__init__(name, level)
        self._verbose = None
        self._dry_run = None
        logging.addLevelName(self.VERBOSE, "VERBOSE")
        logging.addLevelName(self.DRY_RUN, "DRY_RUN")
        self.ready = False

    def _welcome_msg(self):
        self.info("        ---===::: Welcome to ican :::===---")
        self.verbose("--verbose detected.  Displaying verbose messaging.")
        self.dry_run("--dry_run detected.  No files will be modified.")

    def _set_dry_run(self, val=True):
        self._dry_run = val

    def _set_verbose(self, val=True):
        self._verbose = val

    def setup(self, verbose=False, dry_run=False):
        """We call this right away to configure logging.  We will store both
        verbose and dry_run here so we can log verbosely without worry and
        we can use the logger object to determine file writes with the
        property ok_to_write
        """

        console = logging.StreamHandler(sys.stderr)
        if dry_run:
            self._set_dry_run()
            console.setLevel(self.DRY_RUN)
        if verbose:
            self._set_verbose()
            console.setLevel(self.VERBOSE)
        if not verbose and not dry_run:
            console.setLevel(logging.INFO)

        console.setFormatter(IcanFormatter())
        self.addHandler(console)
        self._welcome_msg()
        self.ready = True

    def setup_file_handler(self, filename, format=DEFAULT_FILEHANDLER):
        """This method sets up our filehandler.  This is separate as console
        logging can begin right away but we have to parse the config to get
        the filename for file based logs.
        """

        formatter = logging.Formatter(format, "%m-%d-%Y %H:%M:%S")
        file_handler = logging.FileHandler(filename)
        # File handler gets all messages for now
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.addHandler(file_handler)

    def verbose(self, msg, *args, **kwargs):
        """Custom logging method for our VERBOSE logging level.  Nothing
        special it is just like the stock DEBUG, INFO, etc.
        """

        if self.isEnabledFor(self.VERBOSE):
            self._log(self.VERBOSE, msg, args, **kwargs)

    def dry_run(self, msg, *args, **kwargs):
        """This is a bit unusual.  Dry_run is 15, so someone with
        VERBOSE, 11, would typically get these msgs as well.  But,
        we ONLY want dry_run people to see them, so we have an
        extra if statement built in.
        """

        if self.isEnabledFor(self.DRY_RUN):
            if self._dry_run:
                self._log(self.DRY_RUN, msg, args, **kwargs)

    @property
    def ok_to_write(self):
        """Every module already imports the logger so this was a convenient
        place to globally determine if we can write via the dry_run flag.
        Also we auto-log a msg when this returns false.
        """

        if self._dry_run:
            self.dry_run("Detected --dry_run.  File modification denied.")
            return False
        return True


logging.setLoggerClass(IcanLogger)
logger = logging.getLogger("ican")
