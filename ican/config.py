# -*- coding: utf-8 -*-

import os
from pathlib import Path
from configparser import ConfigParser
from types import SimpleNamespace

from .source import SourceCode
from .pipeline import PipeLine
from .log import logger
from .log import ok_to_write
from .log import setup_file_handler


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
    default_file = dict(file = '*.py',
        style = 'semantic',
        variable = '__version__')

    CONFIG_FILE = '.ican'
    DEFAULT_CONFIG = dict(
        version=default_ver,
        file1=default_file
    )

    def __init__(self, git_root=None):
        self.config_file = None
        self.git_root = git_root
        self.ran_from = Path.cwd()
        self.parser = ConfigParser()

        self.current_version = None
        self.log_to_disk = False
        self.log_file = ''
        self.source_files = []
        self.pipelines = {}
        self.aliases = {}

    @property
    def path(self):
        if self.config_file:
            return self.config_file.parent
        return None

    def ch_dir_root(self):
        """chdir to the config root, so if we run from another dir, relative
        file paths, etc still work as expected.
        """
        if self.git_root:
            os.chdir(str(self.git_root).rstrip('\n'))
        elif self.path:
            os.chdir(str(self.path).rstrip('\n'))

    def persist_version(self, version_str):
        """
        Update the version in the config file then write it so we know the
        new version next time
        """
        logger.debug(f'persisting version - {version_str}')

        self.parser.set('version', 'current', version_str)
        if ok_to_write():
            self.parser.write(open(self.config_file, "w"))

        return None

    def init(self):
        """
        Set default config and save
        """
        logger.debug(f'command init - setting default config')
        self.parser.read_dict(Config.DEFAULT_CONFIG)

        file = Path(self.ran_from, Config.CONFIG_FILE)
        if not ok_to_write():
            config.write(open(file, "w"))
        self.config_file = file
        return

    def search_for_config(self):
        logger.debug(f'searching for config file')
        f = Config.CONFIG_FILE
        dirs = [
            self.git_root,
            self.ran_from,
            self.ran_from.parent,
            self.ran_from.parent.parent
        ]
        for d in dirs:
            if d is None:
                continue
            c = Path(d, f)
            if c.exists():
                self.parser.read(c)
                self.config_file = c
                logger.debug(f'config found @ {c}')
                break
        else:
            msg = f"Could not find config file [{f}]  " \
            "Try using a default config with '--init',"
            raise ValueError(msg)
        return

    def parse(self):
        """
        We search for a config in several locations.  Also, the user may
        specify default config, which we load here as well.
        """

        # By now we may have git_root or config_root
        self.ch_dir_root()

        # Current version
        self.current_version = self.parser.get(
            'version', 'current', fallback='0.1.0'
        )

        # OPTIONS - log file setup
        self.log_to_disk = self.parser.getboolean('options', 'log_to_disk', fallback=False)
        self.log_file = self.parser.get('options', 'log_file', fallback='ican.log')
        if self.log_to_disk:
            setup_file_handler(self.log_file)

        self.parse_source_files()
        self.parse_pipelines()
        self.parse_aliases()

        return

    def parse_aliases(self):
        # aliases
        if not self.parser.has_section('aliases'):
            return

        for alias, built_in in self.parser.items('aliases'):
            cmd_with_args = built_in.strip().split(' ')
            self.aliases[alias] = cmd_with_args
        return

    def parse_pipelines(self):
        # Pipelines
        for s in self.parser.sections():
            if not s.startswith('pipeline:'):
                # Not interested in this section
                continue

            label = s.split(':')[1].strip().lower()
            logger.debug(f'parsing {label.upper()} pipeline')
            list_tuples = self.parser.items(s)

            pl = PipeLine(label=label, steps=list_tuples)
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
