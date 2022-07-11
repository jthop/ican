# -*- coding: utf-8 -*-

from .base import Base
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


class Ican(Base):
    """
    Object which will orchestrate entire program
    """

    def __init__(self):
        """Typically ican will be instantiated by cli with a half parsed
        config.  We pre-parse so logging can begin.
        """
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

    def show(self, style):
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

    def bump(self, part, pre):
        """This is pretty much the full process
        """
        if pre and part == "prerelease":
            logger.verbose(f"Setting prerelease string to {pre}")
        if pre and part != 'prerelease':
            print(pre)
            logger.warning(f"Disregarding --pre with part set to {part.upper()}.")
        logger.verbose(f"Beginning bump of <{part.upper()}>")

        self.version.bump(part, pre)
        logger.verbose(f"New value of <{part.upper()}> - {getattr(self.version, part)}")

        # Update the user's files with new version
        for file in self.config.source_files:
            file.update(self.version)

        # Run the appropriate pipeline
        # new.release, new.prerelease rebuild.release, rebuild.prerelease
        if self.version.stage:
            self.run_pipeline(self.version.stage, True)

        # Once all else is successful, persist the new version
        self.config.persist_version(self.version.semantic)

        return self

    def run_pipeline(self, pipeline, automated=False):
        # Pipeline
        if self.config.pipelines.get(pipeline) is None:
            # Pipeline is not defined
            if automated:
                logger.verbose(f"Pipeline `{pipeline}` not found.")
            else:
                # This was requested so an error is appropriate
                logger.error(f"Pipeline `{pipeline}` not found.")
            return

        pl = self.config.pipelines.get(pipeline)
        pl.run()
        return
