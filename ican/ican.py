# -*- coding: utf-8 -*-

import os
from pathlib import Path

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

        logger.debug('Verbose output selected.')

        # Git init - Do this early incase we need git.root
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
        logger.debug(f'discovered {self.version.semantic} @ CONFIG.version')

        try:
            self.version._git_metadata = self.git.describe()
        except GitDescribeError as e:
            logger.info(e)
            logger.info('Git style versions will be disabled.')
            logger.info('Possibly this is a new repo with no tags.')
            self.git.disable()

        else:
            logger.debug(f'discovered {self.version.git} @ GIT.version')

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

        logger.debug(f'beginning bump of <{part.upper()}>')

        # Use the Version API to bump 'part'
        self.version.bump(part)
        logger.debug(
            f'new value of <{part.upper()}> - {getattr(self.version, part)}'
        )

        # Update the user's files with new version
        for file in self.config.source_files:
            file.update(self.version)

        # Pipeline
        if self.version.new_release:
            if self.config.pipelines.get('release'):
                self.run_pipeline('release')
        elif part == 'build':
            if self.config.pipelines.get('build'):
                self.run_pipeline('build')

        # Once all else is successful, persist the new version
        self.config.persist_version(self.version.semantic)

        return self

    def run_pipeline(self, label):
        logger.debug('RELEASE pipeline triggered')

        pl = self.config.pipelines.get(label)
        ctx = {}
        ctx['tag'] = self.version.tag
        ctx['msg'] = f'auto commit for {self.version.tag}.'
        pl.run(ctx)
