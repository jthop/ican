# -*- coding: utf-8 -*-

import re

from .log import logger


#######################################
#
#   SourceCode - represents a
#     file that we are updating.
#
#######################################


class SourceCode(object):
    def __init__(self, parent, file, regex, style='semantic'):
        self.updated = False
        self.parent = parent
        self.file = file
        self.regex = regex
        self.style = style
        
        if self.regex:
            self.compiled = re.compile(self.regex)

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
            f'Updating `{self.file}` with {self.new_version}'
        )

        with open(self.file, 'r+') as f:
            # Read entire file into string
            original = f.read()

            # Regex search
            updated, n = self.compiled.subn(self._replacement, original, count=1)

            # Check if we found a match or not
            if n == 0:
                logger.debug(f'No match found in {self.file}.')
                return
            logger.debug(f'Found {n} matches.')

            # Write the updated file
            if not self.parent.parent.dry_run:
                f.seek(0)
                f.write(updated)
                f.truncate()

        self.updated = True
        logger.debug(f'Rewrite of file `{self.file}` complete.')
        return True