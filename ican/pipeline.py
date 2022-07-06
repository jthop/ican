# -*- coding: utf-8 -*-
"""
"""
import os
import re
import subprocess
import shlex
from pathlib import Path
from types import SimpleNamespace

from .log import logger
from .log import ok_to_write
from . import exceptions


#######################################
#
#   Pipeline
#
#######################################


class PipeLine(object):

    TEMPLATE = r"{{(?P<var>.*?)}}"

    def __init__(self, label=None, steps=None):
        self.label = label
        self.steps = []
        self.compiled = re.compile(PipeLine.TEMPLATE)

        if steps is None:
            logger.error('must include at least 1 step')

        if steps:
            for k, v in steps:
                logger.debug(f'{label.upper()}.{k} - {v}')
                step = SimpleNamespace(label=k, cmd=v)
                self.steps.append(step)

    def _render(self, cmd, ctx):
        """render jinja-style templates
        {{var}} = ctx['var']
        """

        result, n = self.compiled.subn(
            lambda m: ctx.get(m.group('var'), 'N/A'),cmd
        )

        if n > 0:
            logger.debug(f'rendered cmd: {result}')
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

        logger.debug(f'running cmd - {cmd}')
        result = subprocess.run(
            cmd,
            shell=False,
            capture_output=False,
            text=True
        ).stdout

        if result:
            logger.debug(f'cmd result - {result}')
        return result

    def run(self, ctx={}):
        for step in self.steps:
            cmd = self._render(step.cmd, ctx)
            label = step.label
            if ok_to_write():
                result = self._run_cmd(cmd)
