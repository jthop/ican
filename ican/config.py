# -*- coding: utf-8 -*-

import os
from pathlib import Path
from configparser import ConfigParser
from configparser import DuplicateSectionError
from configparser import ParsingError

from types import SimpleNamespace

from .source import SourceCode
from .pipeline import PipeLine
from .log import logger
from .log import ok_to_write
from .log import setup_file_handler
from .exceptions import NoConfigFound
from .exceptions import DuplicateConfigSections
from .exceptions import ConfigWriteError
from .exceptions import InvalidConfig

#######################################
#
#   Config Class
#
#######################################


class Config(object):
    """
    Object which will orchestrate entire program
    """

    default_ver = dict(current = '0.1.0')
    default_options = dict(log_file = 'ican.log')
    default_file = dict(file = '*.py',
        style = 'semantic',
        variable = '__version__')

    CONFIG_FILE = '.ican'
    DEFAULT_CONFIG = dict(
        version=default_ver,
        options=default_options,
        file1=default_file
    )

    def __init__(self, init=None):
        self.config_file = None
        self.ran_from = Path.cwd()
        self.parser = ConfigParser()

        self.current_version = None
        self.log_file = None
        self.source_files = []
        self.pipelines = {}
        self.aliases = {}
        self.pre_parsed = False
        self.parsed = False

        if init:
            self.init()
        return

    @property
    def path(self):
        if self.config_file:
            return self.config_file.parent
        return None

    @property
    def ready(self):
        if self.parsed and self.pre_parsed and self.config_file:
            return True
        return False

    def ch_dir_root(self):
        """chdir to the config root, so if we run from another dir, relative
        file paths, etc still work as expected.
        """
        if self.path:
            os.chdir(str(self.path).rstrip('\n'))
        return

    def save(self):
        if ok_to_write():
            if not self.config_file:
                f = Path(self.ran_from, Config.CONFIG_FILE)
                self.config_file = f
            try:
                self.parser.write(open(self.config_file, "w"))
                logger.debug('wrote config file')
            except Exception as e:
                raise ConfigWriteError(e)
        return

    def persist_version(self, version_str):
        """
        Update the version in the config file then write it so we know the
        new version next time
        """
        logger.debug(f'persisting version - {version_str}')

        self.parser.set('version', 'current', version_str)
        self.save()
        return

    def init(self):
        """Set default config and save
        """
        logger.debug(f'command init - setting default config')
        self.parser.read_dict(Config.DEFAULT_CONFIG)
        self.save()
        return self

    def search_for_config(self, lazy=False):
        """Find our config file.  Can improve this.
        """
        logger.debug(f'searching for config file')
        f = Config.CONFIG_FILE
        dirs = [
            self.ran_from,
            self.ran_from.parent,
            self.ran_from.parent.parent
        ]
        for d in dirs:
            if d is None:
                continue
            c = Path(d, f)
            if c.exists():
                try:
                    self.parser.read(c)
                except DuplicateSectionError:
                    raise DuplicateConfigSections()
                except ParsingError:
                    raise InvalidConfig()

                self.config_file = c
                logger.debug(f'config found @ {c}')
                break
        else:
            if lazy:
                return
            raise NoConfigFound()
        return

    def pre_parse(self, lazy=False):
        """Get the minimum config needed.  Need log_file so we can log,
        and aliases for the command parser.  Do the rest after commands
        are parsed.
        """

        if not self.config_file:
            self.search_for_config(lazy)

        self.ch_dir_root()
        self.log_file = self.parser.get('options', 'log_file', fallback=None)
        if self.log_file:
            setup_file_handler(self.log_file)
        self.parse_aliases()
        self.pre_parsed = True
        return self

    def parse(self):
        """The parse() method parses the entire config file.  You
        can pre_parse before running parse or not.  Either way it should
        all end up parsed.
        """
        if not self.pre_parsed:
            self.pre_parse()

        self.current_version = self.parser.get(
            'version', 'current', fallback='0.1.0'
        )
        self.parse_source_files()
        self.parse_pipelines()
        self.parsed = True
        return self

    def parse_aliases(self):
        if not self.parser.has_section('aliases'):
            return

        for alias, built_in in self.parser.items('aliases'):
            cmd_with_args = built_in.strip().split(' ')
            self.aliases[alias] = cmd_with_args
        return

    def parse_pipelines(self):
        for s in self.parser.sections():
            if not s.startswith('pipeline:'):
                # Not interested in this section
                continue

            label = s.split(':')[1].strip().lower()
            logger.debug(f'parsing {label.upper()} pipeline')
            left_right_tuple = self.parser.items(s)
            pl = PipeLine(label=label, steps=left_right_tuple)
            self.pipelines[label] = pl
        return

    def parse_source_files(self):
        # FILES TO WRITE
        for s in self.parser.sections():
            if not s.startswith('file:'):
                # Not interested in this section
                continue

            label = s.split(':')[1].strip().lower()
            file = self.parser.get(s, 'file', fallback=None)
            variable = self.parser.get(s, 'variable', fallback=None)
            style = self.parser.get(s, 'style', fallback='semantic')
            regex = self.parser.get(s, 'regex', fallback=None)

            # Instead of raising exp, we can just look for more files
            if file is None:
                logger.debug(f'skipping source - missing file ({label})')
                continue
            elif variable is None and regex is None:
                logger.debug(f'skipping source - missing variable/regex')
                continue

            logger.debug(f'parsing version file {label.upper()}[{file}]')

            # Case with *.py for all python files
            if '*' in file:
                files = self.search_for_files(file)
            else:
                files = [file]
            for f in files:
                u = SourceCode(
                    label,
                    f,
                    style=style,
                    variable=variable,
                    regex=regex
                )
                self.source_files.append(u)

    def search_for_files(self, f):
        """
        First we look in current_dir + all subdirs
        """

        logger.debug(f'* CONFIG: searching for - {f}')

        root = self.path
        #self.debug(f'Searching for {f} in dir {root}')
        matches = [x for x in Path(root).rglob(f)]
        if len(matches) > 0:
            logger.debug(f'found: {len(matches)} files')
            return matches
        return None


