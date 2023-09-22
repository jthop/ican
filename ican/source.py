# -*- coding: utf-8 -*-
"""
"""
import re
from pathlib import Path
import json

from .log import logger
from .exceptions import UserSuppliedRegexError
from .exceptions import SourceCodeFileOpenError
from .exceptions import SourceCodeFileMissing
from .exceptions import VariableRequired
from .exceptions import InvalidStyle

#######################################
#
#   SourceCode - represents a
#     file that we are updating.
#
#######################################


class SourceCode(object):

    # NOTE - below regex is compiled with re.MULTILINE
    VARIABLE_RE = r"^\s*?{{var}}\s*=\s*(?P<quote>[\'\"]?)(?P<version>.+)(?P=quote)"
    
    # Styles
    SEMANTIC = "semantic"
    PUBLIC = "public"
    PEP440 = "pep440"
    GIT = "git"
    VALID_STYLES = [SEMANTIC, PUBLIC, PEP440, GIT]
    
    # File Types
    PYTHON = "python"
    JSON = "json"
    UNKNOWN = "unknown"

    def __init__(self, 
            label, file, style="semantic", variable=None, regex=None, file_type=UNKNOWN):
        """
        Initialize the file we are writing the version to.  File type can be explicitly
        declared in .ican with `file_type` or for the most part can be easily deduced.
        For now, valid values are listed above, PYTHON, JSON, and UNKNOWN.  
        """
        
        self.label = f"{label.upper()}[{file}]"
        self.file = Path(file)
        self.variable = variable
        self.style = style.lower()
        self.regex = regex
        self.file_type = file_type.lower()

        self.updated = False
        self.valid = False
        self.compiled = None

        if not self.file.exists():
            raise SourceCodeFileMissing(
                f"config references non existant file: {self.file}"
            )
        self.valid = True

        if self.style not in self.VALID_STYLES:
            raise InvalidStyle(
                f"Style: {self.style} is not one of {self.VALID_STYLES}.")

    def _finalize(self):
        self.updated = True
        logger.verbose(f"{self.label} - update COMPLETE")
        return True

    def _to_raw_string(self, str):
        return rf"{str}"

    def _replacement(self, match):
        line = match.group(0)
        old_version = match.group("version")
        new_line = line.replace(old_version, self.new_version)

        return new_line

    def _update_python_unknown(self, version):
        """
        This is the method to search via simple txt search or using regex to search
        for the variable to replace in PYTHON/UNKNOWN files.
        """

        # PY/UNKNOWN if we have variable, use it to build a regex
        if self.variable is not None:
            self.regex = SourceCode.VARIABLE_RE.replace("{{var}}", self.variable)
            logger.verbose(f"regex generated for {self.variable}")
        if self.regex:
            try:
                self.compiled = re.compile(self.regex, re.MULTILINE)
            except Exception:
                msg = f"Error compiling regex: {self.regex}"
                raise UserSuppliedRegexError(msg)
            
        with self.file.open("r+") as f:
            # Read entire file into string
            original = f.read()

            # Regex search
            updated, n = self.compiled.subn(
                self._replacement,
                original,
                count=1
            )

            # Check if we found a match or not
            if n == 0:
                logger.verbose(f"{self.label} - NO MATCHES!")
                return
            logger.verbose(f"{self.label} - found {n} matches")

            # Write the updated file
            if logger.ok_to_write:
                f.seek(0)
                f.write(updated)
                f.truncate()

        return self._finalize()

    def _update_json(self, version):
        """
        This method is to update a json file.  These are more structured
        than py or other misc/txt files so search is not needed.  We can parse
        the file and replace the variable if it exists.
        """

        if self.variable is None:
            raise VariableRequired('JSON file must supply VARIABLE name.')
                                         
        # Read json file
        with self.file.open("r") as f:
            data = json.load(f)
        
        # Manipulate the extracted dict
        if data.get(self.variable):
            data[self.variable] = self.new_version
            logger.verbose(
                f"{self.label} - Found and updated variable: {self.variable}.")
        else:
            data[self.variable] = self.new_version
            logger.verbose(
                f"{self.label} - Injected JSON with fresh variable: {self.variable}.")
        
        # Write file
        with self.file.open("w") as f:
            json.dump(data, f, indent=4)

        return self._finalize()

    def update(self, version):
        """
        This wrapper method runs the appropriate update method
        based on the file_type.
        Args:
            version: This is the version object to use as the replacement.
        Returns:
            True if all is successful.  Filename will be updated
            with new version if found.
        """

        # Prep: format the properly styled version to use
        self.new_version = getattr(version, self.style)
        logger.verbose(f"{self.label} - updating to {self.new_version}")

        if self.file_type == self.UNKNOWN:
            logger.verbose(f"{self.label} - UNKNOWN file type. Lets figure this out.")
            if self.file.suffix == ".py":
                self.file_type = self.PYTHON
                logger.verbose(f"{self.label} - detected PYTHON based on extension.")
            elif self.file.suffix == ".json":
                self.file_type = self.JSON
                logger.verbose(f"{self.label} - detected JSON based on extension.")
            else:
                logger.verbose(
                    f"{self.label} - Nothing obvious we will leave as UNKNOWN.")
                # This is the last time we will encounter UNKNOWN, so dispatch now
                return self._update_python_unknown(version)
        
        """Dispatch from here because if the file_type was already known it would
        not have been dispatched above.
        """
        if self.file_type == self.JSON:
            return self._update_json(version)
        elif self.file_type == self.PYTHON:
            return self._update_python_unknown(version)
