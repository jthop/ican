# -*- coding: utf-8 -*-
"""
"""

from . import __version__
from .log import logger


class ExitCode:
    EXPECTED_EXIT = 0

    NO_CONFIG_FOUND = 1
    INVALID_CONFIG = 2
    DUPLICATE_CONFIG_SECTIONS = 3
    DUPLICATE_CONFIG_OPTIONS = 4
    CONFIG_WRITE_ERROR = 5
    NO_CURRENT_VERSION = 6
    ROLLBACK_NOT_POSSIBLE = 7

    GIT_UNUSABLE = 10
    GIT_ROOT_ERROR = 11
    GIT_DESCRIBE_ERROR = 12

    VERSION_PARSE_ERROR = 20
    VERSION_METADATA_ERROR = 21
    VERSION_BUMP_ERROR = 22
    VERSION_PEP440_ERROR = 23
    VERSION_GIT_ERROR = 24

    SOURCE_CODE_FILE_OPEN_ERROR = 30
    SOURCE_CODE_FILE_MISSING = 31
    USER_SUPPLIED_REGEX_ERROR = 32

    PIPELINE_NOT_FOUND = 40
    INVALID_INTERNAL_CMD = 42


class IcanException(Exception):
    def __init__(self, *args, **kwargs):
        """ """
        self.output_method = logger.critical
        self.exit_code = self.__class__.exit_code
        self.msg = ""
        self.e = []

        # Set the message, typically at init
        if args:
            if isinstance(args[0], Exception):
                self.msg = str(args[0])

                _e = args[0]
                if hasattr(_e, "stderr"):
                    stderr = getattr(_e, "stderr")
                    stderr = stderr.decode("utf-8")
                    stderr = stderr.rstrip("\n")
                    self.e.append(stderr)
                if hasattr(_e, "returncode"):
                    returncode = getattr(_e, "returncode")
                    self.e.append(returncode)
            else:
                self.msg = args[0]
        elif hasattr(self.__class__, "msg"):
            self.msg = self.__class__.msg

        # Merge the exit_code, msg, and version
        m = f"{self.msg} (code-{self.exit_code}) v{__version__}"
        self.msg = m

    def __str__(self):
        return self.msg


class DryRunExit(IcanException):
    pass


########################


class NoConfigFound(IcanException):
    exit_code = ExitCode.NO_CONFIG_FOUND
    msg = "Cannot find ican config.  Maybe try `ican init`"


class InvalidConfig(IcanException):
    exit_code = ExitCode.INVALID_CONFIG


class DuplicateConfigSections(IcanException):
    exit_code = ExitCode.DUPLICATE_CONFIG_SECTIONS
    msg = "Duplicate config sections. Look for duplicate file/pipeline labels."


class DuplicateConfigOptions(IcanException):
    exit_code = ExitCode.DUPLICATE_CONFIG_OPTIONS
    msg = "Duplicate config options.  Look for duplicate steps in a pipeline."


class ConfigWriteError(IcanException):
    exit_code = ExitCode.CONFIG_WRITE_ERROR


class NoCurrentVersion(IcanException):
    exit_code = ExitCode.NO_CURRENT_VERSION
    msg = (
        "[NO_VERSION_SPECIFIED]\n"
        "Check if current version is specified in config file, like:\n"
        "version = 0.4.3\n"
    )


class RollbackNotPossible(IcanException):
    exit_code = ExitCode.ROLLBACK_NOT_POSSIBLE
    msg = "Rollback is not possible because no previous version exists."


########################


class GitUnusable(IcanException):
    exit_code = ExitCode.GIT_UNUSABLE


class GitRootError(IcanException):
    exit_code = ExitCode.GIT_ROOT_ERROR


class GitDescribeError(IcanException):
    exit_code = ExitCode.GIT_DESCRIBE_ERROR


########################


class VersionParseError(IcanException):
    exit_code = ExitCode.VERSION_PARSE_ERROR


class VersionMetadataError(IcanException):
    exit_code = ExitCode.VERSION_METADATA_ERROR


class VersionBumpError(IcanException):
    exit_code = ExitCode.VERSION_BUMP_ERROR


class VersionPep440Error(IcanException):
    exit_code = ExitCode.VERSION_PEP440_ERROR


class VersionGitError(IcanException):
    exit_code = ExitCode.VERSION_GIT_ERROR


########################


class SourceCodeFileOpenError(IcanException):
    exit_code = ExitCode.SOURCE_CODE_FILE_OPEN_ERROR


class SourceCodeFileMissing(IcanException):
    exit_code = ExitCode.SOURCE_CODE_FILE_MISSING


class UserSuppliedRegexError(IcanException):
    exit_code = ExitCode.USER_SUPPLIED_REGEX_ERROR


########################


class PipelineNotFound(IcanException):
    exit_code = ExitCode.PIPELINE_NOT_FOUND


class InvalidInternalCmd(IcanException):
    exit_code = ExitCode.INVALID_INTERNAL_CMD

