# -*- coding: utf-8 -*-
"""
"""

import sys

from .log import logger


class ExitCode():
    EXPECTED_EXIT = 0
    
    NO_CONFIG_FOUND = 1
    INVALID_CONFIG = 2
    CONFIG_WRITE_ERROR = 3
    NO_CURRENT_VERSION = 4
    
    GIT_UNUSABLE = 10
    GIT_ADD_ERROR = 11
    GIT_COMMIT_ERROR = 12
    GIT_TAG_ERROR = 13
    GIT_PUSH_ERROR = 14
    GIT_REPO_ERROR = 15
    GPG_SIGNING_ERROR = 16
    
    VERSION_PARSE_ERROR = 20
    VERSION_METADATA_ERROR = 21
    VERSION_BUMP_ERROR = 22
    VERSION_PEP440_ERROR = 23
    VERSION_GIT_ERROR = 24

    SOURCE_CODE_FILE_OPEN_ERROR = 30
    SOURCE_CODE_FILE_MISSING = 31
    USER_SUPPLIED_REGEX_ERROR = 32


class IcanException(Exception):
    def __init__(self, *args, **kwargs):
        """ """
        self.output_method = logger.critical
        self.exit_code = self.__class__.exit_code
        if args:
            self.message = args[0]
        elif hasattr(self.__class__, "message"):
            self.message = self.__class__.message
        else:
            self.message = ""

    def __str__(self):
        return self.message

class DryRunExit(IcanException):
    pass

class NoCurrentVersion(IcanException):
    exit_code = ExitCode.NO_CURRENT_VERSION
    message = (
        "[NO_VERSION_SPECIFIED]\n"
        "Check if current version is specified in config file, like:\n"
        "version = 0.4.3\n"
    )

class SourceCodeFileOpenError(IcanException):
    exit_code = ExitCode.SOURCE_CODE_FILE_OPEN_ERROR

class SourceCodeFileMissing(IcanException):
    exit_code = ExitCode.SOURCE_CODE_FILE_MISSING

class UserSuppliedRegexError(IcanException):
    exit_code = ExitCode.USER_SUPPLIED_REGEX_ERROR