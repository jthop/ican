# -*- coding: utf-8 -*-
"""
"""
import os
import re
import subprocess
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

    TEMPLATE = r"{{(?P<var>.*)}}"

    def __init__(self, label=None, steps=None):
        self.label = label
        self.steps = []
        self.compiled = re.compile(PipeLine.TEMPLATE)

        if steps is None:
            logger.error('- PIPELINE: must include at least 1 step')

        if steps:
            for k, v in steps:
                logger.debug(f'* PIPELINE: {label.upper()}.{k} - {v}')
                step = SimpleNamespace(label=k, cmd=v)
                self.steps.append(step)

    def _render(self, cmd, ctx):
        """render jinja-style templates
        {{var}} = ctx['var']
        """

        result = self.compiled.sub(
            lambda m: ctx.get(
                m.group('var'),
                'MISSING'
            ),
            cmd
        )
        return result

    def _run_cmd(self, cmd=[]):
        env = os.environ.copy()

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            env=env
        ).stdout

        return result

    def run(self, ctx={}):
        for step in self.steps:
            cmd = self._render(step.cmd, ctx)
            label = step.label
            logger.debug(f'PIPELINE: rendered {cmd}')
            if ok_to_write():
                result = self.run_cmd(cmd)