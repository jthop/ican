# -*- coding: utf-8 -*-

import os
from pathlib import Path
from configparser import ConfigParser

from .source import SourceCode
from .log import logger

#######################################
#
#   Config Class
#
#######################################


class Config(object):
    """
    Object which will orchestrate entire program
    """

    ver = dict(current = '0.1.0')
    opt = dict(
        auto_tag = False,
        auto_commit = False,
        auto_push = False,
        signature = False)
    file = dict(file = '*.py',
        style = 'semantic',
        variable = '__version__')

    CONFIG_FILE = '.ican'
    DEFAULT_CONFIG = dict(version=ver, options=opt, file1=file)

    def __init__(self, parent=None):
        self.config_file = None
        self.parent = parent

        self.parser = ConfigParser()
        self.ran_from = Path.cwd()

        self.current_version = None
        self.auto_sign = None
        self.auto_commit = None
        self.auto_push = None
        self.signature = None
        self.source_files = []

    @property
    def path(self):
        if self.config_file:
            return self.config_file.parent
        return None

    def ch_dir_root(self):
        """chdir to the config root, so if we run from another dir, relative
        file paths, etc still work as expected.
        """
        if self.parent.git.root:
            os.chdir(str(self.parent.git.root).rstrip('\n'))
        elif self.path:
            os.chdir(str(self.path).rstrip('\n'))

    def persist_version(self, version_str):
        """
        Update the version in the config file then write it so we know the
        new version next time
        """
        logger.debug(f'Persisting version {version_str} in config file.')
        
        self.parser.set('version', 'current', version_str)
        if not self.parent.dry_run:
            self.parser.write(open(self.config_file, "w"))

        return None

    def init(self):
        """
        Set default config and save
        """
        self.parser.read_dict(Config.DEFAULT_CONFIG)

        file = Path(self.ran_from, Config.CONFIG_FILE)
        if not self.parent.dry_run:
            config.write(open(file, "w"))
        self.config_file = file
        return

    def search_for_config(self):
        f = Config.CONFIG_FILE
        dirs = [
            self.parent.git.root,
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

        # Loop through config to debug it if --verbose
        for section in self.parser.sections():
            logger.debug(f'* Config section parsed: --== {section} ==--')
            for name, value in self.parser.items(section):
                logger.debug(f'* {name} = {value}')

        # Current version
        self.current_version = self.parser.get(
            'version', 'current', fallback='0.1.0'
        )

        # OPTIONS
        self.auto_tag = self.parser.getboolean('options', 'auto-tag', fallback=False)
        self.auto_commit = self.parser.getboolean('options', 'auto-commit', fallback=False)
        self.auto_push = self.parser.getboolean('options', 'auto-push', fallback=False)
        self.signature = self.parser.getboolean('options', 'signature', fallback=False)

        o = 'auto_tag={} auto_commit={} auto_push={} signature={}'.format(
            self.auto_tag,
            self.auto_commit,
            self.auto_push,
            self.signature
        )
        logger.debug(f'Options parsed.  {o}')

        # We need to verify sections are there, especially before we blindly remove

        self.parse_source_files()

        return None

    def parse_source_files(self):
        # FILES TO WRITE
        sections = self.parser.sections().copy()
        sections.remove('version')
        sections.remove('options')
        for s in sections:
            file = self.parser.get(s, 'file', fallback=None)
            variable = self.parser.get(s, 'variable', fallback=None)
            style = self.parser.get(s, 'style', fallback='semantic')
            regex = self.parser.get(s, 'regex', fallback=None)

            # Instead of raising exp, we can just look for more files
            if file is None :
                logger.debug(f'Skipping {s}, missing file reference')
                continue
            elif variable is None and regex is None:
                logger.debug(f'Skipping {s}, found no variable or regex config')
                continue

            # Case with *.py for all python files
            if '*' in file:
                files = self.search_for_files(file)
                for f in files:
                    u = SourceCode(
                        self,
                        f,
                        style=style,
                        variable=variable,
                        regex=regex
                    )
                    self.source_files.append(u)
            # This is the normal case, 1 file per section
            else:
                u = SourceCode(
                    self,
                    file,
                    style=style,
                    variable=variable,
                    regex=regex
                )
                self.source_files.append(u)

    def search_for_files(self, f):
        """
        First we look in current_dir + all subdirs
        """

        logger.debug(f'Config parser searching for: {f}')

        root = self.path
        #self.debug(f'Searching for {f} in dir {root}')
        matches = [x for x in Path(root).rglob(f)]
        if len(matches) > 0:
            logger.debug(f'Config parser found: {len(matches)} files')
            return matches
        return None
