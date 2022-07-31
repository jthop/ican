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
from collections import UserDict

from .log import logger
from .base import Base

from .exceptions import InvalidInternalCmd


##########################
#  CTX
##########################


class CTX(UserDict):

    ARG_W_DEFAULT = "arg_(?P<num>\d+)(?P<default_operator>\|\|)(?P<default>.*)"
    ARG = r"{arg_(?P<num>\d+)}"

    def __init__(self, *args, **kwargs):
        self._defaults = {}
        super().__init__(*args, **kwargs)

    def __missing__(self, key):
        match = re.search(self.ARG_W_DEFAULT, key)
        if match:
            num = match.group('num')
            default = match.group('default')
            if f'arg_{num}' in self.data:
                return self.data[f'arg_{num}']
            else:
                return default

    def __setitem__(self, item, value):
        # Make sure it's a string
        value = str(value)
        super().__setitem__(item, value)

    def gen_env(self):
        env = {f'ICAN_{k.upper()}': v for k, v in self.items()}
        return {**os.environ, **env}


##########################
#  Step
##########################


class Step:

    COMMANDS = r"\$ICAN\(\s*?(?P<cmd>.*?)\s*?\)"
    CLI = "__CLI__"
    INTERNAL = "__INTERNAL__"

    def __init__(self, label, cmd):
        self.label = label
        self.cmd = None
        self.backup = None
        self.type = None

        match = re.search(self.COMMANDS, cmd)
        if match:
            self.cmd = match.group("cmd")
            self.type = self.INTERNAL
        else:
            self.cmd = cmd
            self.type = self.CLI

    def is_internal(self):
        if self.type == self.INTERNAL:
            return True
        return False

    def is_cli(self):
        if self.type == self.CLI:
            return True
        return False

    def render(self, ctx):
        """render template variables
        """

        formatted = self.cmd.format_map(ctx)
        if formatted != self.cmd:
            self.backup = self.cmd
            self.cmd = formatted
            logger.verbose(f"rendered cmd: {formatted}")
        return


##########################
#  Pipeline
##########################


class Pipeline(Base):

    ARGS = r"{arg_(?P<num>\d+)}"
    CLI = "__CLI__"
    INTERNAL = "__INTERNAL__"
    INTERNAL_CMDS = {
        'bump': 'bump',
        'run': 'run_pipeline',
        'pre': 'pre',
        'rollback': 'rollback',
        'show': 'show',
    }

    def __init__(self, label=None, steps=None):
        self.label = label
        self.steps = []
        self.env = None
        self.ctx = None

        if steps is None:
            logger.error("must include at least 1 step")

        for k, v in steps:
            logger.verbose(f"{label.upper()}.{k} - {v}")
            step = Step(k, v)
            self.steps.append(step)

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
        command = parts[0].lower()
        if command not in self.INTERNAL_CMDS.keys():
            raise InvalidInternalCmd()

        # list comprehension so we don't supply an arg of None or ""
        args = [x for x in parts[1:] if x]
        # Run using same dispatch method as cli
        getattr(self.ican, self.INTERNAL_CMDS.get(command))(*args)

        return

    def _build_ctx(self, user_args):
        """ """

        ctx = CTX()
        ctx["version"] = self.version.semantic
        ctx["semantic"] = self.version.semantic
        ctx["public"] = self.version.public
        ctx["pep440"] = self.version.pep440
        ctx["git"] = self.version.git
        ctx["tag"] = self.version.tag
        ctx["major"] = self.version.major
        ctx["minor"] = self.version.minor
        ctx["patch"] = self.version.patch
        ctx["prerelease"] = self.version.prerelease
        ctx["build"] = self.version.build
        ctx["env"] = self.version.env
        ctx["age"] = self.version.age
        ctx["root"] = self.config.path
        ctx["previous"] = self.config.previous_version

        # include the user_args
        x = 0
        for arg in user_args:
            x += 1
            ctx[f"arg_{x}"] = arg

        # Use the ctx to generate a new env
        self.env = ctx.gen_env()

        logger.verbose(f"Generated env/ctx: {ctx}")
        return ctx

    def run(self, user_args):
        logger.alt_info(f"+BEGIN pipeline.{self.label.upper()}")
        for step in self.steps:
            # Rebuild the ctx each step
            ctx = self._build_ctx(user_args)

            # ctx as arg to step, step renders the template
            step.render(ctx)
            logger.alt_info(F"+RUNNING step.{step.type.upper()}<{step.cmd}>")
            # The final step, run the step.  Use the appropriate run
            if step.is_internal():
                self._run_internal(step)
            if step.is_cli():
                self._run_cli_cmd(step)

        logger.alt_info(f"+END pipeline.{self.label.upper()}")
        return
