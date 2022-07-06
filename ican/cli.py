# -*- coding: utf-8 -*-
"""
from tempfile import NamedTemporaryFile
"""

import argparse
import sys

from . import __version__
from .config import Config
from .ican import Ican
from .log import logger
from .log import setup_console_handler
from .emojis import rnd_good_emoji
from .exceptions import IcanException


#===============================
#
#  CLI Class
#
#===============================


class CLI(object):
    usage="""ican <command> [<args>]

Some of our most popular commands:
   bump [PART]      increment the PART of the version
                    [minor, major, patch, prerelease, build]
   show [STYLE]     display current version with STYLE
                    [semantic, public, pep440, git]
   init             initialize the current directory with a 
                    config file
"""

    def __init__(self):
        self._register_excepthook()
        self._arg_pop()
        if '--version' not in sys.argv:
            self.config = Config()
            self.config.pre_parse()
            self._substitute_aliases()

        parser = argparse.ArgumentParser(
            description='ican - version bumper and lightweight build pipelines',
            usage=CLI.usage,
            prog='ican'
        )
        parser.add_argument('command', help='command-specific-arguments')    # need
        parser.add_argument(
            '--version', 
            action='version',
            help='display ican version',
            version=f'ican v{__version__}'
        )

        # now parse our updated args
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            # no method for the command
            logger.error('Unrecognized command')
            parser.print_help()
            exit(1)

        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()
        return

    def _arg_pop(self):
        """Here we will pop --verbose and --dry_run out asap,
        that way logging can be setup before we parse the config
        file, etc.
        """

        verbose = False
        dry_run = False

        for i in range(1, len(sys.argv)):
            if sys.argv[i] == '--verbose':
                verbose = True
                sys.argv.pop(i)
            elif sys.argv[i] == '--dry_run':
                dry_run = True
                sys.argv.pop(i)
        setup_console_handler(verbose, dry_run)
        return

    def _substitute_aliases(self):
        """At this point we have parsed the config and know any
        user-defined aliases.  We need to substitute them into
        sys.argv for a seamless alias experience.
        """

        aliases = self.config.aliases
        # if config.alias was used, insert it into sys.argv
        if len(sys.argv) < 2:
            # nothing to substitute here because no command
            return
        command = sys.argv[1]
        if aliases.get(command):
            built_in = aliases.get(command)
            sys.argv.pop(1)   #delete the alias command
            sys.argv[1:1] = built_in
        return

    def _register_excepthook(self):
        """Register our custom exception handler
        """

        self._original_excepthook = sys.excepthook
        sys.excepthook = self._excepthook
        return

    def _excepthook(self, type, value, tracekback, debug=False):
        """Custom exception handler
        """

        if isinstance(value, IcanException):
            if value.msg:
                value.output_method(value.msg)
            if value.e:
                for line in value.e:
                    value.output_method(line)
            if debug:
                self._original_excepthook(type, value, tracekback)
            exit_code = value.exit_code
            sys.exit(exit_code)
        else:
            self._original_excepthook(type, value, tracekback)

    def bump(self):
        """dispatched here with command bump
        """

        parser = argparse.ArgumentParser(
            description='increment the [PART] of the version')
        parser.add_argument(
            "part", 
            nargs='?',
            default='build',
            choices=['major', 'minor', 'patch', 'prerelease', 'build'],
            help="what to bump"
        )
        args = parser.parse_args(sys.argv[2:])

        i = Ican(config=self.config)
        i.bump(args.part.lower())
        logger.debug('bump() COMPLETE')
        logger.warning(f'Version: {i.version.semantic}')

        return

    def show(self):
        """dispatched here with command show
        """

        parser = argparse.ArgumentParser(
            description='show the [STYLE] of current version')
        parser.add_argument(
            "style", 
            nargs='?',
            default='semantic',
            choices=['semantic', 'public', 'pep440', 'git'],
            help="version style to show"
        )
        args = parser.parse_args(sys.argv[2:])

        i = Ican(config=self.config)
        v = i.show(args.style)
        logger.debug('show() COMPLETE')
        logger.warning(v)

        return

    def init(self):
        """dispatched here with command init
        """

        parser = argparse.ArgumentParser(
            description='initialize your project in the current directory')
        args = parser.parse_args(sys.argv[2:])

        c = Config(init=True).parse()
        i = Ican(config=c)
        logger.warning('init COMPLETE')

        return

    def test(self):
        """dispatched here with command test
        """

        parser = argparse.ArgumentParser(description='test')
        parser.add_argument(
            "first",
            nargs='?',
            help="first test arg"
        )
        args = parser.parse_args(sys.argv[2:])
        print(f'10-4 with arg {args.first}')


def entry():
    CLI()

