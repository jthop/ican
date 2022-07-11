# -*- coding: utf-8 -*-
"""

 ,---.  ,-.,---.  ,---.  ,-.    ,-..-. .-.,---.
 | .-.\ |(|| .-.\ | .-'  | |    |(||  \| || .-'
 | |-' )(_)| |-' )| `-.  | |    (_)|   | || `-.
 | |--' | || |--' | .-'  | |    | || |\  || .-'
 | |    | || |    |  `--.| `--. | || | |)||  `--.
 /(     `-'/(     /( __.'|( __.'`-'/(  (_)/( __.'
(__)      (__)   (__)    (_)      (__)   (__)


"""

import os
import re
import subprocess
import shlex
from pathlib import Path
from types import SimpleNamespace

from .log import logger
from . import exceptions


#######################################
#
#   Pipeline
#
#######################################


class Pipeline(object):

    TEMPLATE = r"{{(?P<var>.*?)}}"

    def __init__(self, label=None, steps=None):
        self.label = label
        self.steps = []
        self.compiled = re.compile(Pipeline.TEMPLATE)

        if steps is None:
            logger.error('must include at least 1 step')

        if steps:
            for k, v in steps:
                logger.verbose(f'{label.upper()}.{k} - {v}')
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
            logger.verbose(f'rendered cmd: {result}')
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

        #my_env = {**os.environ, **dict_with_env_variables}
        
        if type(cmd) not in (tuple, list):
            cmd = shlex.split(cmd)

        logger.verbose(f'running cmd - {cmd}')
        result = subprocess.run(
            cmd,
            shell=False,
            capture_output=False,
            text=True
        ).stdout

        if result:
            logger.verbose(f'cmd result - {result}')
        return result

    def run(self, ctx={}):
        logger.info(f'+BEGIN pipeline.{self.label.upper()}')
        for step in self.steps:
            cmd = self._render(step.cmd, ctx)
            label = step.label
            if logger.ok_to_write:
                result = self._run_cmd(cmd)
        logger.info(f'+END pipeline.{self.label.upper()}')
