# -*- coding: utf-8 -*-
"""
from tempfile import NamedTemporaryFile
"""

import argparse
import sys

from . import __version__
from .ican import Ican
from .log import logger
from .log import set_logger_level
from .emojis import rnd_good_emoji
from .exceptions import IcanException


#===============================
#
#  CLI Class
#
#===============================


class CLI(object):
    usage='''ican <command> [<args>]

We recommend the following commands:
   bump [PART]      increment the PART of the version
                    [minor, major, patch, prerelease, build]
   show [STYLE]     display current version with STYLE
                    [semantic, public, pep440, git]
   init             initialize the current directory with a 
                    config file
'''

    def __init__(self):
        self._register_excepthook()

        parser = argparse.ArgumentParser(
            description='ican - bump versions, git, docker',
            usage=CLI.usage,
            prog='ican'
        )

        parser.add_argument('command', help='Subcommand to run')    # need
        parser.add_argument(
            '--version', 
            action='version',
            version=f'ican v{__version__}'
        )
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail

        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            logger.error('Unrecognized command')
            parser.print_help()
            exit(1)

        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()
        
        return

    def _register_excepthook(self):
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._excepthook

    def _excepthook(self, type, value, tracekback, debug=False):
        """ """
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

    def fetch_args(self, parser):
        """
        now that we're inside a subcommand, ignore the first
        TWO argvs, ie the command (git) and the subcommand (commit)
        """
        
        args = vars(parser.parse_args(sys.argv[2:]))

        self.verbose = False
        self.dry_run = False
        if args.get('verbose'):
            self.verbose = args['verbose']
        if args.get('dry_run'):
            self.dry_run = args['dry_run']

        set_logger_level(self.verbose, self.dry_run)

        return args

    def bump(self):
        parser = argparse.ArgumentParser(
            description='increment the [PART] of the version')
        
        parser.add_argument(
            "part", 
            nargs='?',
            default='build',
            choices=['major', 'minor', 'patch', 'prerelease', 'build'],
            help="what to bump"
        )
        parser.add_argument('--dry-run', action="store_true")
        parser.add_argument('--verbose', action="store_true")
        args = self.fetch_args(parser)
        
        part = args['part']
        i = Ican(self.dry_run)
        i.bump(part.lower())
        logger.warning(f'Version: {i.version.semantic}')

        return


    def show(self):
        parser = argparse.ArgumentParser(
            description='show the [STYLE] of current version')

        parser.add_argument(
            "style", 
            nargs='?',
            default='semantic',
            choices=['semantic', 'public', 'pep440', 'git'],
            help="version style to show"
        )
        parser.add_argument('--verbose', action="store_true")
        args = self.fetch_args(parser)

        i = Ican(self.dry_run)
        v = i.show(args['style'])
        logger.warning(v)

        return


    def init(self):
        parser = argparse.ArgumentParser(
            description='initialize your project in the current directory')
        parser.add_argument('--dry-run', action="store_true")
        parser.add_argument('--verbose', action="store_true")
        args = self.fetch_args(parser)

        i = Ican(self.dry_run, init=True)
        logger.warning('init complete')

        return


def entry():
    CLI()

