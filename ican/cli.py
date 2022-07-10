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
from .emojis import rnd_good_emoji
from .exceptions import IcanException


#===============================
#
#  CLI Class
#
#===============================


class CLI(object):
    usage="""ican <COMMAND> [<ARGS>]

commands:
  bump [PART]      increment version [minor, major, patch, prerelease, build]
  show [STYLE]     show version [semantic, public, pep440, git]
  run [PIPELINE]   run the specified PIPELINE
  status [STATE]   set the version STATUS [alpha, beta, rc, dev, release, post]
  rollback         restore the previous version
  init             initialize a config in the current directory
"""

    def __init__(self):
        self._register_excepthook()
        self._arg_pop()
        if '--version' not in sys.argv:
            self.config = Config()
            self.config.pre_parse()
            self._substitute_aliases()

        parser = argparse.ArgumentParser(usage=CLI.usage,prog='ican')
        parser.add_argument('--dry_run',help='do not write any files', action='store_true')
        parser.add_argument('--verbose',help='display debug information', action='store_true')
        parser.add_argument('command', help=argparse.SUPPRESS)
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
                break
        for i in range(1, len(sys.argv)):
            if sys.argv[i] == '--dry_run':
                dry_run = True
                sys.argv.pop(i)
                break
        logger.setup(verbose, dry_run)
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
            description='PART choices [major, minor, patch, prerelease, build]',
            usage='ican bump [PART]')
        parser.add_argument(
            "part", 
            nargs='?',
            default='build',
            choices=['major', 'minor', 'patch', 'prerelease', 'build'],
            help=argparse.SUPPRESS
        )
        # add --dry_run and --verbose only to be included in --help
        parser.add_argument('--dry_run',help='do not write any files', action='store_true')
        parser.add_argument('--verbose',help='display debug information', action='store_true')
        args = parser.parse_args(sys.argv[2:])

        i = Ican(config=self.config)
        i.bump(args.part.lower())
        logger.verbose('bump() COMPLETE')
        logger.info(f'Version: {i.version.semantic}')

        return

    def show(self):
        """dispatched here with command show
        """

        parser = argparse.ArgumentParser(
            description='STYLE choices [semantic, public, pep440, git]',
            usage='ican show [STYLE]')
        parser.add_argument(
            "style", 
            nargs='?',
            default='semantic',
            choices=['semantic', 'public', 'pep440', 'git'],
            help=argparse.SUPPRESS
        )
        # add --verbose only to be included in --help
        parser.add_argument('--verbose',help='display debug information', action='store_true')
        args = parser.parse_args(sys.argv[2:])

        i = Ican(config=self.config)
        v = i.show(args.style)
        logger.info(f'Current {args.style} version: {v}')

        return

    def rollback(self):
        """in case of emergency, restore the previously
        persisted version.
        """

        parser = argparse.ArgumentParser(usage='ican rollback')
        # add --dry_run and --verbose only to be included in --help
        parser.add_argument('--dry_run',help='do not write any files', action='store_true')
        parser.add_argument('--verbose',help='display debug information', action='store_true')
        args = parser.parse_args(sys.argv[2:])

        i = Ican(config=self.config)
        i.rollback()
        logger.verbose('rollback() COMPLETE')
        logger.info(f'Rollback: {i.version.semantic}')

    def init(self):
        """dispatched here with command init
        """

        parser = argparse.ArgumentParser(usage='ican init')
        # add --dry_run and --verbose only to be included in --help
        parser.add_argument('--dry_run',help='do not write any files', action='store_true')
        parser.add_argument('--verbose',help='display debug information', action='store_true')
        args = parser.parse_args(sys.argv[2:])

        c = Config(init=True).parse()
        i = Ican(config=c)
        logger.info('init COMPLETE')

        return

    def run(self):
        """dispatched here with command init
        """

        parser = argparse.ArgumentParser(
            description='PIPELINE can be any pipeline defined in your .ican file.',
            usage='ican run [PIPELINE]')
        parser.add_argument(
            "pipeline",
            help=argparse.SUPPRESS
        )
        # add --verbose only to be included in --help
        parser.add_argument('--dry_run',help='do not write any files', action='store_true')
        parser.add_argument('--verbose',help='display debug information', action='store_true')
        args = parser.parse_args(sys.argv[2:])

        i = Ican(config=self.config)
        logger.info(f'+BEGIN pipeline[{args.pipeline}].run')
        i.run_pipeline(args.pipeline)
        logger.info(f'+END pipeline[{args.pipeline}].run')

    def test(self):
        """dispatched here with command test
        """

        parser = argparse.ArgumentParser(usage='ican test [ARGS]')
        # add --dry-run and --verbose only to be included in --help
        parser.add_argument('--dry-run',help='do not write any files', action='store_true')
        parser.add_argument('--verbose',help='display debug information', action='store_true')
        parser.add_argument("first", nargs='?', help=argparse.SUPPRESS)
        args = parser.parse_args(sys.argv[2:])
        logger.verbose('verbose')
        print(f'10-4 with arg {args.first}')

def entry():
    CLI()

