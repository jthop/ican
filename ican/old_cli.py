# -*- coding: utf-8 -*-
"""
from tempfile import NamedTemporaryFile
"""

import argparse

from . import __version__
from .ican import Ican
from .log import logger
from .log import set_logger_level
from .emojis import rnd_good_emoji
from .exceptions import register_excepthook

arg_desc = f'''\
===================================
       Ican v{__version__}
===================================

usage:
$ bump [options] VERSION_SEGMENT
where VERSION_SEGMENT is:
[major, minor, patch, prerelease, build]
'''


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # bump
    parser_bump = subparsers.add_parser('bump', help='bump --help')
    parser_bump.add_argument(
        "part", 
        nargs='?',
        default='build',
        choices=['major', 'minor', 'patch', 'prerelease', 'build'],
        help="what to bump"
    )
    parser_bump.add_argument('--dry-run', action="store_true")
    parser_bump.add_argument('--verbose', action="store_true")

    # show
    parser_show = subparsers.add_parser('show', help='display current values')
    parser_show.add_argument(
        "style", 
        nargs='?',
        default='semantic',
        choices=['semantic', 'public', 'pep440', 'git'],
        help="version style to display"
    )

    # init
    parser_init = subparsers.add_parser('init', help='initialize a config for this project')
    parser_init.add_argument(
        "style", 
        nargs='?',
        default='semantic',
        choices=['semantic', 'public', 'pep440', 'git'],
        help="version style to display"
    )
    
    args = vars(parser.parse_args())

    # We can setup logger as soon as we have args
    set_logger_level(args['verbose'])
    # Rest of args

    print(args)

def old():
    """
    The script entrypoint
    """

    register_excepthook()

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=arg_desc,
        prog='ican'
    )

    # The primary argument
    parser.add_argument(
        "part", 
        nargs='?',
        default='build',
        choices=['major', 'minor', 'patch', 'prerelease', 'build'],
        help="what to bump"
    )
    # is_canonical
    parser.add_argument(
        "--canonical", action="store_true",
        help = "True/False is the current pep440 of this version canonical"
    )
    # current flag
    parser.add_argument(
        '--current', action='store_true',
        help='display the current semantic version'
    )
    # default config
    parser.add_argument(
        "--defaults", action="store_true",
        help = "use default config to run without a config file"
    )
    # dry-run flag
    parser.add_argument(
        "--dry-run", action="store_true",
        help = "dry run - will not modify files - best with --verbose"
    )
    # git flag
    parser.add_argument(
        "--git", action="store_true",
        help = "display the current git version"
    )
    # pep440 flag
    parser.add_argument(
        "--pep440", action="store_true",
        help = "display the current pep440 version"
    )
    # public flag
    parser.add_argument(
        '--public', action='store_true',
        help='display the current public version'
    )
    # verbose flag
    parser.add_argument(
        "--verbose", action="store_true",
        help = "verbose output"
    )
    # version flag
    parser.add_argument(
        '--version', 
        action='version',
        version=f'{rnd_good_emoji(2)} ican v{__version__} {rnd_good_emoji(2)}'
    )


    # The meat of the cli, parse the args
    args = vars(parser.parse_args())

    # We can setup logger as soon as we have args
    set_logger_level(args['verbose'])

    # Rest of args
    part = args['part']

    canonical = args['canonical']   
    git = args['git']
    current = args['current']
    public = args['public']
    pep440 = args['pep440']

    #verbose, dry_run, defaults, config_file in args{}
    i = Ican(args=args)

    if current:
        logger.warning(f'Current: {i.version.semantic} {rnd_good_emoji(2)}')
    elif git:
        logger.warning(f'Git: {i.version.git} {rnd_good_emoji(2)}')
    elif public:
        logger.warning(f'Public: {i.version.public} {rnd_good_emoji(2)}=')
    elif pep440:
        logger.warning(f'Pep440: {i.version.pep440} {rnd_good_emoji(2)}')
    elif canonical:
        c = b.version.is_canonical()
        logger.warning(f'Pep440 (canonical={c}): {i.version.pep440}') 
    else:
        i.bump(part.lower())
        logger.warning(f'{rnd_good_emoji(2)} Version: {i.version.semantic} {rnd_good_emoji(2)}')
        



if __name__ == "__main__":
    main()

