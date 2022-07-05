# -*- coding: utf-8 -*-
"""
from tempfile import NamedTemporaryFile
"""

import argparse
import sys

from . import __version__
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
    usage='''ican <command> [<args>]

Some of our most popular commands:
   bump [PART]      increment the PART of the version
                    [minor, major, patch, prerelease, build]
   show [STYLE]     display current version with STYLE
                    [semantic, public, pep440, git]
   init             initialize the current directory with a 
                    config file
'''

    def __init__(self):
        self._register_excepthook()
        self.i = Ican()
        self.aliases = self.i.config.aliases

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

        # if config.alias was used, insert it into sys.argv
        command = sys.argv[1]
        if self.aliases.get(command):
            built_in = self.aliases.get(command)
            sys.argv.pop(1)   #delete the alias command
            sys.argv[1:1] = built_in

        # now parse our upsated args
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            # no method for the command
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
        
        parser.add_argument(
            '--dry-run',
            help='files will not be written - best with --verbose',
            action="store_true"
        )
        parser.add_argument(
            '--verbose',
            help='display all debug information available',
            action="store_true"
        )
        args = vars(parser.parse_args(sys.argv[2:]))
        setup_console_handler(args['verbose'], args['dry_run'])

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
        args = self.fetch_args(parser)
        part = args['part']

        self.i.bump(part.lower())
        logger.debug('bump() COMPLETE')
        logger.warning(f'Version: {self.i.version.semantic}')

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
        args = self.fetch_args(parser)

        v = self.i.show(args['style'])
        logger.debug('show() COMPLETE')
        logger.warning(v)

        return

    def init(self):
        parser = argparse.ArgumentParser(
            description='initialize your project in the current directory')
        args = self.fetch_args(parser)

        del self.i
        self.i = Ican(init=True)
        logger.warning('init COMPLETE')

        return

    def test(self):
        parser = argparse.ArgumentParser(description='test')
        parser.add_argument(
            "first",
            nargs='?',
            help="first test arg"
        )
        args = self.fetch_args(parser)
        print(f'10-4 with arg {args["first"]}')


def entry():
    CLI()

