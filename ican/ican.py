# -*- coding: utf-8 -*-

import os
from pathlib import Path

from . import __version__
from .config import Config
from .version import Version
from .git import Git
from .log import logger
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

    @property
    def dry_run(self):
        if self.dryrun:
            logger.info('Skipping file write due to --dry-run')
            return True
        return False

    def __init__(self, dry_run=None, init=False):
        self.dryrun = dry_run

        self.version = None
        self.git = None
        self.config = None

        logger.debug(f'   ---=== Welcome to ican v{__version__} ===---')
        logger.debug('Verbose output selected.')
        if self.dryrun:
            logger.info('--dry-run detected.  No files will be written to.')
        
        # Git init - Do this early incase we need git.root
        logger.debug('Investigating a project git repo.')
        self.git = Git()

        # Create config obj.  If init, set defaults.
        # Otherwise, search for existing config file.
        self.config = Config(parent=self)
        if init:
            self.config.init()
        else:
            self.config.search_for_config()

        # Now we have default or existing config, we can parse
        self.config.parse()

        # Now config is parsed.  We can parse from config
        self.version = Version.parse(self.config.current_version)
        logger.debug(f'Parsed version {self.version.semantic} from config')

        try:
            self.version._git_metadata = self.git.describe()
        except GitDescribeError as e:
            logger.info(e)
            logger.info('Git style versions will be disabled.')
            logger.info('Possibly this is a new repo with no tags.')
            self.git.disable()
            
        else:
            logger.debug(f'Set git-version metadata: {self.version.git}')

        return

    def show(self, style):
        """
        Show the <STYLE> version
        """

        v = getattr(self.version, style)
        if v is None:
            return f'version style: {style} not available'
        return v


    def bump(self, part):
        """
        This is pretty much the full process
        """

        logger.debug(f'Beginning bump of `{part}`...')

        # Use the Version API to bump 'part'
        self.version.bump(part)
        logger.debug(f'+ New value of {part}: {getattr(self.version, part)}')

        for file in self.config.source_files:
            file.update(self.version)

        # Write the new version to config file
        self.config.persist_version(self.version.semantic)

        # Pipeline
        if self.version.new_release:
            # The actual auto_commit and auto_tag
            if self.config.auto_commit and not self.dry_run:
                self.git.add()
                self.git.commit(f'auto-commit triggered by version bump')

            if self.config.auto_tag and not self.dry_run:
                msg = f'auto-generated release: {self.version.semantic}'
                self.git.tag(self.version.tag, self.config.signature, msg)

            if self.config.auto_push and not self.dry_run:
                self.git.push(self.version.tag)

        return self
