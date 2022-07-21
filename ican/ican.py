# -*- coding: utf-8 -*-

from .base import Base
from .version import Version
from .git import Git
from .log import logger
from .exceptions import GitDescribeError
from .exceptions import NoConfigFound
from .exceptions import RollbackNotPossible
from .exceptions import PipelineNotFound


#######################################
#
#   Bump Class
#
#######################################


class Ican(Base):
    """
    Object which will orchestrate entire program
    """

    def __init__(self, only_pre_parse=False):
        """Typically ican will be instantiated by cli with a half parsed
        config.  We pre-parse so logging can begin.
        """
        self.ready = False

        # make sure the config is fully parsed
        if not self.config.pre_parsed:
            # Typically 'init' is the ONLY way to be in this state
            self.config.parse()
        elif not self.config.parsed and not only_pre_parse:
            self.config.parse()
        # Here if still config not ready, it will never be ready
        if not self.config.config_file:
            raise NoConfigFound()

        # Now config is parsed.  We can parse from config
        self.version = Version.parse(self.config.current_version)
        logger.verbose(f"discovered {self.version.semantic} @ CONFIG.version")

        # Git init
        self.git = Git()

        try:
            self.version._git_metadata = self.git.describe()
        except GitDescribeError as e:
            logger.verbose(e)
            logger.verbose("Git-versions are disabled. Does this repo have a tag?")
            self.git.disable()
        else:
            logger.verbose(f"Discovered {self.version.git} @ GIT.version")
        return

    def pre(self, token):
        """Set the prerelease token"""

        logger.verbose(f"Setting prerelease string to {token}")
        self.version.set_prerelease_token(token)

        # Save the new version, config will check for dry_run
        self.config.persist_version(self.version.semantic)

    def show(self, style="semantic"):
        """
        Show the <STYLE> version
        """

        v = getattr(self.version, style)
        if v is None:
            return f"Version STYLE: {style} not available"
        return v

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

    def bump(self, part="build", token=None):
        """This is pretty much the full process"""
        if token:
            logger.verbose(f"Setting prerelease string to {token}")
        logger.verbose(f"Beginning bump of <{part.upper()}>")

        self.version.bump(part, token)
        logger.verbose(
            f"New value of <{part.upper()}> - {getattr(self.version, part)}"
        )

        # Update the user's files with new version
        for file in self.config.source_files:
            file.update(self.version)

        # Once all else is successful, persist the new version
        self.config.persist_version(self.version.semantic)

        return self

    def run_pipeline(self, pipeline):
        # Pipeline
        if self.config.pipelines.get(pipeline) is None:
            # Pipeline is not defined
            raise PipelineNotFound(f'pipeline.{pipeline.upper()} not found')

        pl = self.config.pipelines.get(pipeline)
        pl.run()
        return
