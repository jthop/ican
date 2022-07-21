# -*- coding: utf-8 -*-
"""

   ___ ___  _  _ ___ ___ ___
  / __/ _ \| \| | __|_ _/ __|
 | (_| (_) | .` | _| | | (_ |
  \___\___/|_|\_|_| |___\___|.py

"""

import os
from pathlib import Path
from configparser import ConfigParser
from configparser import DuplicateSectionError
from configparser import DuplicateOptionError
from configparser import ParsingError
from collections import OrderedDict

from .base import Base
from .source import SourceCode
from .pipeline import Pipeline
from .log import logger
from .exceptions import DuplicateConfigSections
from .exceptions import DuplicateConfigOptions
from .exceptions import ConfigWriteError
from .exceptions import InvalidConfig


#######################################
#
#   Config Class
#
#######################################


class MultiOrderedDict(OrderedDict):
    """Custom obj to use as parser storage to allow multiple
    keys with same keyname. Credit:
    https://stackoverflow.com/questions/15848674/
    """
    def __setitem__(self, key, value):
        if isinstance(value, list) and key in self:
            self[key].extend(value)
        else:
            # super(MultiOrderedDict, self).__setitem__(key, value)
            super().__setitem__(key, value)


class Config(Base):
    """Config object for entire program
    """

    default_ver = dict(current="0.1.0")
    default_options = dict(log_file="ican.log")
    default_file = dict(file="*.py", style="semantic", variable="__version__")

    CONFIG_FILE = ".ican"
    DEFAULT_CONFIG = dict(
        version=default_ver, options=default_options, file1=default_file
    )

    def __init__(self, init=False):
        self.config_file = None
        self.ran_from = Path.cwd()
        self.parser = ConfigParser()

        self.current_version = None
        self.previous_version = None
        self.log_file = None
        self.source_files = []
        self.pipelines = {}
        self.pre_parsed = False
        self.parsed = False

        if init:
            self.init()
        return

    @property
    def path(self):
        if self.config_file:
            return self.config_file.parent.absolute()
        return None

    def ch_dir_root(self):
        """chdir to the config root, so if we run from another dir, relative
        file paths, etc still work as expected.
        """
        if self.path:
            os.chdir(str(self.path).rstrip("\n"))
        return

    def save(self):
        if logger.ok_to_write:
            if not self.config_file:
                f = Path(self.ran_from, Config.CONFIG_FILE)
                self.config_file = f
            try:
                self.parser.write(open(self.config_file, "w"))
                logger.verbose("wrote config file")
            except Exception as e:
                raise ConfigWriteError(e)
        return

    def persist_version(self, new_version):
        """Update the version in the config file then write it so we
        know the new version next time.  Save previous in case
        we need it to rollback.
        """
        logger.verbose(f"persisting version - {new_version}")
        self.parser.set("version", "previous", self.current_version)
        self.parser.set("version", "current", new_version)
        self.save()
        self.current_version = new_version
        return

    def init(self):
        """Set default config and save"""
        logger.verbose("cmd: init - setting default config")
        self.parser.read_dict(Config.DEFAULT_CONFIG)
        self.save()
        return self

    def locate_config_file(self):
        """Find our config file."""
        logger.verbose("Searching for config file")
        f = Config.CONFIG_FILE
        dir = Path.cwd()
        root = Path(dir.root)
        while True:
            cfg = Path(dir, f)
            if cfg.exists():
                self.config_file = cfg
                logger.verbose(f"Config found @ {cfg}")
                return True
            dir = dir.parent
            if dir == root:
                # quit right before we'd be writing in the root
                logger.verbose("Cannot find config file!")
                break
        return None

    def pre_parse(self):
        """Partially parse the config.  Enough to log and grab the version.
        """

        if not self.config_file:
            # Only time we could already have self.config_file is if we
            # ran an init
            if not self.locate_config_file():
                # Silently continue on.  There is still a chance for init()
                return self
            try:
                self.parser.read([self.config_file])
            except DuplicateSectionError as e:
                raise DuplicateConfigSections(e)
            except DuplicateOptionError as e:
                raise DuplicateConfigOptions(e)
            except ParsingError as e:
                raise InvalidConfig(e)

        self.current_version = self.parser.get(
            "version",
            "current",
            fallback="0.1.0"
        )
        self.previous_version = self.parser.get(
            "version",
            "previous",
            fallback=[None]
        )
        self.log_file = self.parser.get(
            "options",
            "log_file",
            fallback=[None]
        )

        self.ch_dir_root()
        if self.log_file:
            logger.setup_file_handler(self.log_file)
        self.pre_parsed = True
        return self

    def parse(self):
        """The parse() method parses the entire config file.  You
        can pre_parse before running parse or not.  Either way it should
        all end up parsed.
        """
        if not self.pre_parsed:
            self.pre_parse()

        self.parse_source_files()
        self.parse_pipelines()
        self.parsed = True
        return self

    def parse_pipelines(self):
        for s in self.parser.sections():
            if not s.startswith("pipeline:"):
                # Not interested in this section
                continue

            label = s.split(":")[1].strip().lower()
            logger.verbose(f"parsing {label.upper()} pipeline")
            left_right_tuple = self.parser.items(s)
            pl = Pipeline(label=label, steps=left_right_tuple)
            self.pipelines[label] = pl
        return

    def parse_source_files(self):
        # FILES TO WRITE
        for s in self.parser.sections():
            if not s.startswith("file:"):
                # Not interested in this section
                continue

            label = s.split(":")[1].strip().lower()
            file = self.parser.get(s, "file", fallback=None)
            style = self.parser.get(s, "style", fallback="semantic")
            variable = self.parser.get(s, "variable", fallback=None)
            regex = self.parser.get(s, "regex", fallback=None)

            # Instead of raising exp, we can just look for more files
            if file is None:
                logger.verbose(f"skipping source - missing file ({label})")
                continue
            elif variable is None and regex is None:
                logger.verbose("Skipping source - missing variable/regex")
                continue

            logger.verbose(f"parsing file config {label.upper()}[{file}]")
            # Case with *.py for all python files
            if "*" in file:
                files = self._find_wildcard_filename(file)
            else:
                files = [file]
            for f in files:
                u = SourceCode(label, f, style=style, variable=variable, regex=regex)
                self.source_files.append(u)

    def _find_wildcard_filename(self, f):
        """Search for all files if config has '*' in the
        filename field.  Search root dir + all subdirs.
        """

        logger.verbose(f"file section * in filename - {f}")
        matches = [x for x in Path(self.path).rglob(f)]
        if matches:
            logger.verbose(f"wildcard found: {len(matches)} files")
            return matches
        return None
