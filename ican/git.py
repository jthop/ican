# -*- coding: utf-8 -*-

import subprocess
import os

from pathlib import Path
from tempfile import NamedTemporaryFile
from types import SimpleNamespace

from .log import logger


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
            r = str(self.root).rstrip('\n')
            logger.debug(f'Found git root: {r}')


    def command(self, cmd=[]):
        env = os.environ.copy()
        try:
            result = subprocess.run(
                cmd, 
                check=True, 
                capture_output=True,
                env=env
            ).stdout
        except subprocess.CalledProcessError as e:
            print("Exception: {e.returncode}, {e.output}")
            return None
        return result


    def is_usable(self):
        """
        Simple test to check if git is installed and can
        be used.
        """

        cmd = ['git', 'rev-parse', '--git-dir']
        try:
            u = self.command(cmd)
        except Exception as e:
            return False

        return u


    def find_root(self):
        """
        Find the git root
        Returns:
            Returns: pathlib.Path instance of the root git dir if found.
        """

        cmd = ['git', 'rev-parse', '--show-toplevel']
        dir = self.command(cmd)
        
        return Path(dir.decode())


    def describe(self):
        """
        get info about the latest tag in git
        """

        cmd = ['git', 'describe', '--dirty', '--tags', '--long']
        d = self.command(cmd).decode().split("-")
        
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


    def add(self, files='.'):
        """
        Wrapper to git add.
        Arguments:
            files: the files to add.  Defaults to '.' which is all

        Returns:
            Will return the results of the cli command.
        """

        cmd = ['git', 'add', files]
        add = self.command(cmd)

        return add


    def push(self, tag):
        """
        Wrapper to git add.
        Arguments:
            tag: the tag_name to push the commit with.

        Returns:
            Will return the results of the cli command
        """

        cmd = ['git', 'push', 'origin', 'master', tag]
        push = self.command(cmd)


    def commit(self, message):
        """
        Wrapper to create git commits.
        """

        with NamedTemporaryFile("wb", delete=False) as f:
            f.write(message.encode("utf-8"))

        cmd = ['git', 'commit', '-F', f.name]
        commit = self.command(cmd)

        return commit


    def tag(self, tag_name, sign=False, message=None):
        """
        Create a git tag.
        Arguments:
            tag_name(required): the tag name to use - ie: version
            sign: sign the tag? True/False
            message: message to attach to the tag
        Returns:
            Will return the results of the cli command
        """

        cmd = ["git", "tag", "-a", tag_name]
        if sign:
            cmd += ["--sign"]
        if message:
            cmd += ["--message", message]

        tag = self.command(cmd)
        return tag
