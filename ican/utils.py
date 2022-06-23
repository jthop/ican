# -*- coding: utf-8 -*-

import os
import re
from pathlib import Path

from . import logger

version_re = re.compile(
    r"__version__\s*=\s*(?P<quote>[\'\"])(?P<version>.+)(?P=quote)"
)


#######################################
#
#   Misc utils
#
#######################################

def read_file(f):
    return Path(f).read_text()

def parse_version_from_file(f):
    """
    Often times the only record of current_version is inside
    a source file such as __init__.py
    """

    file_txt = read_file(f)
    #self.debug(f'Opened and read file: {f} to memory.')

    match = version_re.search(file_txt, re.MULTILINE)
    if match is None:
        raise ValueError('Could not find __version__ in __init__.py.')
    #self.debug(f'Found potential version: {match.group(1)}.')

    return match.group(1)

def search_for_files(f, root):
    # First we look in current_dir + all subdirs
    root = config_root
    #self.debug(f'Searching for {f} in dir {root}')
    matches = [x for x in Path(root).rglob(f)]
    if len(matches) > 0:
        return matches