# -*- coding: utf-8 -*-
"""
"""
import re
from pathlib import Path

from .log import logger
from .log import ok_to_write
from . import exceptions
from .exceptions import UserSuppliedRegexError
from .exceptions import SourceCodeFileOpenError
from .exceptions import SourceCodeFileMissing

#######################################
#
#   SourceCode - represents a
#     file that we are updating.
#
#######################################


class SourceCode(object):

    VARIABLE_RE = r"{{var}}\s*=\s*(?P<quote>[\'\"])(?P<version>.+)(?P=quote)"

    def __init__(self, label, file, style='semantic', variable=None, regex=None):
        self.label = f'{label.upper()}[{file}]'
        self.file = Path(file)
        self.variable = variable
        self.style = style
        self.regex = regex

        self.updated = False
        self.valid = False
        
        if not self.file.exists():
            raise SourceCodeFileMissing(
                f'config references non existant file: {self.file}'
            )
        self.valid = True

        if variable is not None:
            self.regex = SourceCode.VARIABLE_RE.replace("{{var}}", variable)
            logger.debug(f'regex generated for {variable}')

        if self.regex:
            try:
                self.compiled = re.compile(self.regex)
            except Exception as e:
                msg = f'Error compiling regex: {self.regex}'
                raise UserSuppliedRegexError(msg)

    def _to_raw_string(self, str):
        return fr"{string}"

    def _replacement(self, match):
        line = match.group(0)
        old_version = match.group('version')
        new_line = line.replace(old_version, self.new_version)
        
        return new_line

    def update(self, version):
        """
        his method performs an inplace file update.  
        Args:
            filename: The file to run the substitution on
        Returns:
            True if all is successful.  Filename will be updated
            with new version if found.
        """

        self.new_version = getattr(version, self.style)
        logger.debug(
            f'{self.label} - updating to {self.new_version}'
        )

        try:
            f = self.file.open('r+')
        except OSError:
            raise SourceCodeFileOpenError(f'Error opening {self.file}')

        with self.file.open('r+') as f:
            # Read entire file into string
            original = f.read()

            # Regex search
            updated, n = self.compiled.subn(self._replacement, original, count=1)

            # Check if we found a match or not
            if n == 0:
                logger.debug(f'{self.label} - NO MATCHES!')
                return
            logger.debug(f'{self.label} - found {n} matches')

            # Write the updated file
            if ok_to_write():
                f.seek(0)
                f.write(updated)
                f.truncate()

        self.updated = True
        logger.debug(f'{self.label} - update COMPLETE')
        return True
