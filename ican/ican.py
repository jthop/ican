# -*- coding: utf-8 -*-

import os
from pathlib import Path

from . import __version__
from .config import Config
from .version import Version
from .git import Git
from .log import logger
from .emojis import rnd_good_emoji

#######################################
#
#   Bump Class
#
#######################################


class Ican(object):
    """
    Object which will orchestrate entire program
    """

    def __init__(self, dry_run=None):
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

        # Config
        self.config = Config(parent=self)
        self.config.parse()

        # Now config is parsed.  We can parse from config
        self.version = Version.parse(self.config.current_version)
        logger.debug(
            f'{rnd_good_emoji(2)} Parsed version {self.version.semantic}' \
            f' from config {rnd_good_emoji(2)}'
        )

        self.version._git_metadata = self.git.describe()
        logger.debug(
            f'{rnd_good_emoji(2)} Set git-version metadata: ' \
            f'{self.version.git} {rnd_good_emoji(2)}'
        )

        return

    @property
    def dry_run(self):
        if self.dryrun:
            logger.info('Skipping file write due to --dry-run')
            return True
        return False

    def bump(self, part):
        """
        This is pretty much the full process
        """

        logger.debug(f'Beginning bump of `{part}`...')

        # Use the Version API to bump 'part'
        self.version.bump(part)
        logger.debug(f'+ New value of {part}: {getattr(self.version, part)}.')

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
