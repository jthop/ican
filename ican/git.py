# -*- coding: utf-8 -*-

import subprocess
import os

from pathlib import Path
from types import SimpleNamespace

from .log import logger
from .exceptions import GitDescribeError
from .exceptions import GitRootError

#######################################
#
#   Git Class
#
#######################################


"""
commit message keywords borrowed from python-semantic-release

feat: A new feature. (minor)
fix: A bug fix. (patch)
docs: Documentation changes. (build)
style: Changes that do not affect the meaning of the code
    (white-space, formatting, missing semi-colons, etc). (build)
refactor: A code change that neither fixes a bug nor adds a feature. (build)
perf: A code change that improves performance. (patch)
test: Changes to the test framework. (build)
build: Changes to the build process or tools. (build)
"""


class Git(object):
    """
    Simple class to communicate with git via subprocess git commands.
    The other alternative is to use python-git which is big and rarely
    already installed.
    """

    def __init__(self):
        # First we'll initialize some variables
        self.usable = None
        self.root = None

        # Now we can test git, get root_dir, and describe
        self.usable = self.is_usable()
        if self.usable:
            self.root = self.find_root()
            r = str(self.root).rstrip("\n")
            logger.verbose(f"found git root @ {r}")

    def disable(self):
        self.usable = False

    def command(self, cmd=[]):
        env = os.environ.copy()

        result = subprocess.run(cmd, check=True, capture_output=True, env=env).stdout

        return result

    def is_usable(self):
        """
        Simple test to check if git is installed and can
        be used.
        """

        cmd = ["git", "rev-parse", "--git-dir"]
        try:
            u = self.command(cmd)
        except Exception:
            return False

        return u

    def find_root(self):
        """
        Find the git root
        Returns:
            Returns: pathlib.Path instance of the root git dir if found.
        """

        cmd = ["git", "rev-parse", "--show-toplevel"]
        try:
            dir = self.command(cmd)
        except Exception as e:
            raise GitRootError(e)

        return Path(dir.decode())

    def describe(self):
        """
        get info about the latest tag in git
        """

        cmd = ["git", "describe", "--dirty", "--tags", "--long"]
        try:
            d = self.command(cmd).decode().split("-")
        except Exception as e:
            raise GitDescribeError(e)

        dirty = False
        if d[-1].strip() == "dirty":
            dirty = True
            d.pop()

        commit_sha = d.pop().lstrip("g")
        distance = int(d.pop())
        tag = "-".join(d).lstrip("v")

        g = SimpleNamespace(
            tag=tag,
            commit_sha=commit_sha,
            distance=distance,
            dirty=dirty,
        )
        return g
