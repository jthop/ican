
class ExitCode(enum.IntEnum):
    EXPECTED_EXIT = 0
    NO_CONFIG_FOUND = 1
    NO_CURRENT_VERSION = 2
    GIT_UNUSABLE = 3
    GIT_ADD_ERROR = 4
    GIT_COMMIT_ERROR = 5
    GIT_TAG_ERROR = 6
    GIT_PUSH_ERROR = 7
    GIT_REPO_ERROR = 8
    GPG_SIGNING_ERROR = 9
    VERSION_PARSE_ERROR = 10
    VERSION_BUMP_ERROR = 11
    INVALID_CONFIG = 12
    CONFIG_WRITE_ERROR = 13
    DOCKER_BUILD_ERROR = 14
    DOCKER_UP_ERROR = 15
    DOCKER_DOWN_ERROR = 16
    FILE_IO_ERROR = 17
    NO_PERMISSION = 18


class DeployException(Exception):
    def __init__(self, *args, **kwargs):
        self.exit_code = self.__class__.exit_code
        if args:
            self.message = args[0]
        elif hasattr(self.__class__, "message"):
            self.message = self.__class__.message
        else:
            self.message = ""

    def __str__(self):
        return self.message

class DryRunExit(DeployException):
    pass


class NoneIncrementExit(DeployException):
    exit_code = ExitCode.NO_INCREMENT


class NoCommitizenFoundException(DeployException):
    exit_code = ExitCode.NO_COMMITIZEN_FOUND