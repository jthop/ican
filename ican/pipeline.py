# -*- coding: utf-8 -*-

#
#   ,---.  ,-.,---.  ,---.  ,-.    ,-..-. .-.,---.
#   | .-.\ |(|| .-.\ | .-'  | |    |(||  \| || .-'
#   | |-' )(_)| |-' )| `-.  | |    (_)|   | || `-.
#   | |--' | || |--' | .-'  | |    | || |\  || .-'
#   | |    | || |    |  `--.| `--. | || | |)||  `--.
#   /(     `-'/(     /( __.'|( __.'`-'/(  (_)/( __.'
#  (__)      (__)   (__)    (_)      (__)   (__)
#

import os
import re
import subprocess
import functools
import shlex
from types import SimpleNamespace

from .log import logger
from .base import Base

from .exceptions import InvalidInternalCmd


#######################################
#
#   Pipeline
#
#######################################


class Pipeline(Base):

    TEMPLATE = r"{{\s*?(?P<var>.*?)\s*?}}"
    COMMANDS = r"\$_ICAN{\s*?(?P<cmd>.*?)\s*?}"
    INTERNAL_CMDS = ['bump', 'run', 'pre', 'rollback', 'show']

    def __init__(self, label=None, steps=None):
        self.label = label
        self.steps = []
        self.env = None
        self.ctx = None

        if steps is None:
            logger.error("must include at least 1 step")

        if steps:
            for k, v in steps:
                logger.verbose(f"{label.upper()}.{k} - {v}")
                step = SimpleNamespace(label=k, cmd=v, typ=None, backup=None)
                self.steps.append(step)

    def _parse_step(self, step):
        """Strip out the internal cmd for {% cmd %} style commands.
        This method sets the cmd.typ for the step as well.
        """

        # Match here means this is internal command, not CLI
        match = re.search(self.COMMANDS, step.cmd)
        if match:
            step.cmd = match.group("cmd")
            step.typ = "ICAN"
            return
        step.typ = "CLI"
        return

    def _render_template(self, step):
        """render jinja-style templates
        {{var}} = ctx['var']
        """

        # If we make it to here this is CLI command
        result, n = re.subn(
            self.TEMPLATE,
            lambda m: self.ctx.get(m.group("var").upper(), "N/A"),
            step.cmd
        )
        if n > 0:
            step.backup = step.cmd
            step.cmd = result
            logger.verbose(f"rendered cmd: {result}")
        return

    def _run_cli_cmd(self, step):
        """Here is where we actually run the cli commands.
        Args:
            cmd: This should be a tuple or list of command, args such as:
            ['git', 'commit', '-a']

        Returns:
            result: the result object will have attributes of both
            stdout and stderr representing the results of the subprocess
        """
        if not logger.ok_to_write:
            return

        if type(step.cmd) not in (tuple, list):
            step.cmd = shlex.split(step.cmd)
        logger.verbose(f"running cmd - {step.cmd}")
        result = subprocess.run(
            step.cmd,
            shell=False,
            env=self.env,
            capture_output=False,
            text=True
        ).stdout

        if result:
            logger.verbose(f"cmd result - {result}")
        return

    def _run_internal(self, step):
        """This is for pipelines with itnernal commands.  Such as:
        $_ICAN{bump build} runs version.bump('build')
        """
        if not logger.ok_to_write:
            return

        logger.verbose(f"running internal cmd - {step.cmd}")
        parts = step.cmd.split(' ')
        cmd = parts[0].lower()
        if cmd not in self.INTERNAL_CMDS:
            raise InvalidInternalCmd()

        cmds = {
            'bump': 'bump',
            'rollback': 'rollback',
            'pre': 'pre',
            'run': 'run_pipeline'
        }
        args = parts[1:]
        # Run using same dispatch method as cli
        getattr(self.ican, cmds.get(cmd))(*args)

        return

    def _build_ctx(self):
        """ """
        self.ctx = {}
        self.ctx["VERSION"] = self.version.semantic
        self.ctx["SEMANTIC"] = self.version.semantic
        self.ctx["PUBLIC"] = self.version.public
        self.ctx["PEP440"] = self.version.pep440
        self.ctx["GIT"] = self.version.git
        self.ctx["TAG"] = self.version.tag
        self.ctx["MAJOR"] = self.version.major
        self.ctx["MINOR"] = self.version.minor
        self.ctx["PATCH"] = self.version.patch
        self.ctx["PRERELEASE"] = self.version.prerelease
        self.ctx["BUILD"] = self.version.build
        self.ctx["ENV"] = self.version.env
        self.ctx["AGE"] = self.version.age
        self.ctx["ROOT"] = self.config.path
        self.ctx["PREVIOUS"] = self.config.previous_version

        # ensure all are strings
        for k, v in self.ctx.items():
            self.ctx[k] = str(v)

        logger.verbose(f"Generated ctx: {self.ctx}")
        return

    def _build_env(self):
        """ Use ctx and simple add prefix to all keys
        """

        _env = {f'ICAN_{k}': v for k, v in self.ctx.items()}
        self.env = {**os.environ, **_env}
        return

    def run(self):
        logger.info(f"+BEGIN pipeline.{self.label.upper()}")
        for step in self.steps:
            # Rebuild the ctx each step
            self._build_ctx()
            self._build_env()
            # Parse cli from internal
            self._parse_step(step)
            if step.typ == "ICAN":
                self._run_internal(step)
            if step.typ == "CLI":
                # CLI cmds need template rendering first
                self._render_template(step)
                self._run_cli_cmd(step)
        logger.info(f"+END pipeline.{self.label.upper()}")
