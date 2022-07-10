# -*- coding: utf-8 -*-

import os
from pathlib import Path

from .config import Config
from .version import Version
from .git import Git
from .log import logger
from .exceptions import GitDescribeError
from .exceptions import NoConfigFound
from .exceptions import RollbackNotPossible

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
        """Typically ican will be instantiated by cli with a half parsed
        config.  We pre-parse so logging can begin.
        """
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
        if not self.config.config_file:
            raise NoConfigFound()

        # Now config is parsed.  We can parse from config
        self.version = Version.parse(self.config.version)
        logger.verbose(f'discovered {self.version.semantic} @ CONFIG.version')

        # Git init
        self.git = Git()

        try:
            self.version._git_metadata = self.git.describe()
        except GitDescribeError as e:
            logger.info(e)
            logger.info('Git style versions will be disabled.')
            logger.info('Possibly this is a new repo with no tags.')
            self.git.disable()
        else:
            logger.verbose(f'discovered {self.version.git} @ GIT.version')
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
        """This is pretty much the full process
        """

        logger.verbose(f'beginning bump of <{part.upper()}>')

        # Use the Version API to bump 'part'
        self.version.bump(part)
        logger.verbose(
            f'new value of <{part.upper()}> - {getattr(self.version, part)}'
        )

        # Update the user's files with new version
        for file in self.config.source_files:
            file.update(self.version)

        # Run the appropriate pipeline
        if self.version.new_release:
            self.run_pipeline('release')
        elif part == 'prerelease':
            self.run_pipeline('prerelease')
        elif part == 'build':
            self.run_pipeline('build')

        # Once all else is successful, persist the new version
        self.config.persist_version(self.version.semantic)

        return self

    def rollback(self):
        """When all else fails, this should bring the version back
        to your prior saved version.  It will also update all source
        files you have configured.
        """
        if not self.config.previous_version:
            raise RollbackNotPossible()

        # delete old, create new self.version
        del self.version
        self.version = Version.parse(self.config.previous_version)

        # Update the source files
        for file in self.config.source_files:
            file.update(self.version)

        # Now that everything else is finished, persist version
        self.config.persist_version(self.config.previous_version)

    def run_pipeline(self, pipeline):
        # Pipeline
        if self.config.pipelines.get(pipeline) is None:
            return

        logger.verbose(f'running pipeline.{pipeline.upper()}')
        pl = self.config.pipelines.get(pipeline)

        # Prep the ctx dictionary
        ctx = dict()
        vars = dir(self.version)
        for v in vars:
            if not v.startswith('_') and not callable(getattr(self.version, v)):
                ctx[v] = getattr(self.version, v)
        pl.run(ctx)
        return

