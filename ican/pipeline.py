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
import shlex
from types import SimpleNamespace

from .log import logger
from .base import Base


#######################################
#
#   Pipeline
#
#######################################


class Pipeline(Base):

    TEMPLATE = r"{{(?P<var>.*?)}}"

    def __init__(self, label=None, steps=None):
        self.label = label
        self.steps = []
        self.env = None
        self.ctx = None
        self.compiled = re.compile(Pipeline.TEMPLATE)

        if steps is None:
            logger.error("must include at least 1 step")

        if steps:
            for k, v in steps:
                logger.verbose(f"{label.upper()}.{k} - {v}")
                step = SimpleNamespace(label=k, cmd=v)
                self.steps.append(step)

    def _render(self, cmd):
        """render jinja-style templates
        {{var}} = ctx['var']
        """

        result, n = self.compiled.subn(
            lambda m: self.ctx.get(m.group("var").upper(), "N/A"), cmd
        )

        if n > 0:
            logger.verbose(f"rendered cmd: {result}")
        return result

    def _run_cmd(self, cmd):
        """Here is where we actually run the pipeline steps via the
        shell.

        Args:
            cmd: This should be a tuple or list of command, args such as:
            ['git', 'commit', '-a']

        Returns:
            result: the result object will have attributes of both
            stdout and stderr representing the results of the subprocess
        """

        if type(cmd) not in (tuple, list):
            cmd = shlex.split(cmd)

        logger.verbose(f"running cmd - {cmd}")
        result = subprocess.run(
            cmd, shell=False, env=self.env, capture_output=False, text=True
        ).stdout

        if result:
            logger.verbose(f"cmd result - {result}")
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
        self.ctx["STAGE"] = self.version.stage
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
        self._build_ctx()
        self._build_env()
        logger.info(f"+BEGIN pipeline.{self.label.upper()}")
        for step in self.steps:
            cmd = self._render(step.cmd)
            # label = step.label
            if logger.ok_to_write:
                self._run_cmd(cmd)
        logger.info(f"+END pipeline.{self.label.upper()}")
