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
from .exceptions import ConfigNotReady

#######################################
#
#   Bump Class
#
#######################################


class Ican(object):
    """
    Object which will orchestrate entire program
    """

    def __init__(self, config=None):
        self.version = None
        self.git = None
        self.config = config
        self.ready = False

        # make sure the config is fully parsed
        if not self.config.pre_parsed:
            self.config.parse()
        elif not self.config.parsed:
            self.config.parse()
        # Here if still config not ready, it will never be ready
        if not self.config.ready:
            raise ConfigNotReady()

        # Git init - Do this early incase we need git.root
        self.git = Git()

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

        # Run the appropriate pipeline
        self.run_pipeline(part)

        # Once all else is successful, persist the new version
        self.config.persist_version(self.version.semantic)

        return self

    def run_pipeline(self, part):
        # Pipeline
        if self.version.new_release and self.config.pipelines.get('release'):
            pll = 'release'
        elif part == 'build' and self.config.pipelines.get('build'):
            pll = 'build'
        else:
            return

        logger.debug(f'running pipeline.{pll.upper()}')
        pl = self.config.pipelines.get(pll)

        # Prep the ctx dictionary
        ctx = dict()
        vars = dir(self.version)
        for v in vars:
            if not v.startswith('_') and not callable(getattr(self.version, v)):
                ctx[v] = getattr(self.version, v)
        pl.run(ctx)
        return

