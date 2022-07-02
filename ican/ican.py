# -*- coding: utf-8 -*-

import os
from pathlib import Path

from . import __version__
from .config import Config
from .version import Version
from .git import Git
from .log import logger
from .log import ok_to_write
from .emojis import rnd_good_emoji
from .exceptions import GitDescribeError

#######################################
#
#   Bump Class
#
#######################################


class Ican(object):
    """
    Object which will orchestrate entire program
    """

    def __init__(self, init=False):
        self.version = None
        self.git = None
        self.config = None

        logger.debug(f'   ---=== Welcome to ican v{__version__} ===---')
        logger.debug('* ICAN: Verbose output selected.')

        # Git init - Do this early incase we need git.root
        logger.debug('* ICAN: searching for project git repo.')
        self.git = Git()

        # Create config obj.  If init, set defaults.
        # Otherwise, search for existing config file.
        self.config = Config(self.git.root)
        if init:
            self.config.init()
        else:
            self.config.search_for_config()

        # Now we have default or existing config, we can parse
        self.config.parse()

        # Now config is parsed.  We can parse from config
        self.version = Version.parse(self.config.current_version)
        logger.debug(f'* ICAN: parsed version {self.version.semantic} from config')

        try:
            self.version._git_metadata = self.git.describe()
        except GitDescribeError as e:
            logger.info(e)
            logger.info('Git style versions will be disabled.')
            logger.info('Possibly this is a new repo with no tags.')
            self.git.disable()

        else:
            logger.debug(f'* ICAN: found git metadata: {self.version.git}')

        return

    def show(self, style):
        """
        Show the <STYLE> version
        """

        v = getattr(self.version, style)
        if v is None:
            return f'version STYLE: {style} not available'
        return v

    def bump(self, part):
        """
        This is pretty much the full process
        """

        logger.debug(f'+ ICAN: beginning BUMP of {part.upper()}')

        # Use the Version API to bump 'part'
        self.version.bump(part)
        logger.debug(f'+ ICAN: new value of {part}: {getattr(self.version, part)}')

        # Update the user's files with new version
        for file in self.config.source_files:
            file.update(self.version)

        # Pipeline
        if self.version.new_release:
            if self.config.pipelines.get('release'):
                self.run_pipeline('release')


        # Once all else is successful, persist the new version
        self.config.persist_version(self.version.semantic)

        return self

    def run_pipeline(self, label):
        logger.debug('+ ICAN: RELEASE pipeline triggered')

        pl = self.config.pipelines.get(label)
        ctx = {}
        ctx['tag'] = self.version.tag
        ctx['msg'] = f'auto commit for {self.version.tag}.'
        pl.run(ctx)
