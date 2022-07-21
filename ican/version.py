# -*- coding: utf-8 -*-

import re
from types import SimpleNamespace
from .log import logger


__version__ = "0.4"


#########################
#
#   Version Class
#
#########################


class Version(object):
    """
    Semver representation
    """

    BUMPABLE = ["major", "minor", "patch", "prerelease", "build"]
    DEFAULT_PRERELEASE = "alpha.0"
    DEFAULT_BUILD = "build.0"

    last_number_re = re.compile(r"(?:[^\d]*(\d+)[^\d]*)+")
    semver_re = re.compile(
        r"""
            ^(?P<major>0|[1-9]\d*)
            \.(?P<minor>0|[1-9]\d*)
            \.(?P<patch>0|[1-9]\d*)
            (?:-(?P<prerelease>
                (?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)
                (?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*
            ))?
            (?:\+(?P<build>
                [0-9a-zA-Z-]+
                (?:\.[0-9a-zA-Z-]+)*
            ))?$
        """,
        re.VERBOSE,
    )
    pep440_re = re.compile(
        r"""
        ^([1-9][0-9]*!)?
        (0|[1-9][0-9]*)
        (\.(0|[1-9][0-9]*))*((a|b|rc)(0|[1-9][0-9]*))?
        (\.post(0|[1-9][0-9]*))?
        (\.dev(0|[1-9][0-9]*))?$
        """,
        re.VERBOSE,
    )

    def __init__(self, major=0, minor=0, patch=0, prerelease=None, build=None):

        self._major = int(major)
        self._minor = int(minor)
        self._patch = int(patch)
        self._prerelease = prerelease
        self._build = build
        self._git_metadata = None

        f = SimpleNamespace(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            prerelease=self.prerelease,
            build=self.build,
            semantic=self.semantic,
            part=None,
        )
        self._frozen = f

    def __str__(self):
        return self.semantic

    def __repr__(self):
        address = hex(id(self))
        return f"<Version {self.semantic} at {address}>"

    ##########################################
    #
    #  Version Parts:
    #    major, minor, patch, pre, build
    #
    ##########################################

    @property
    def major(self):
        return self._major

    @major.setter
    def major(self, value):
        raise AttributeError("major is readonly")

    @property
    def minor(self):
        return self._minor

    @minor.setter
    def minor(self, value):
        raise AttributeError("minor is readonly")

    @property
    def patch(self):
        return self._patch

    @patch.setter
    def patch(self, value):
        raise AttributeError("patch is readonly")

    @property
    def prerelease(self):
        return self._prerelease

    @prerelease.setter
    def prerelease(self, value):
        raise AttributeError("prerelease is readonly")

    @property
    def build(self):
        return self._build

    @build.setter
    def build(self, value):
        raise AttributeError("build is readonly")

    @property
    def build_int(self):
        """
        Parse an int from build...
        +build.102 = 102
        """

        if not self.build:
            return 0
        match = Version.last_number_re.search(self.build)
        if match:
            return int(match.group(1))

    @property
    def prerelease_int(self):
        """
        Parse an int from prerelease...
        """

        if not self.prerelease:
            return None
        match = Version.last_number_re.search(self.prerelease)
        if match:
            return int(match.group(1))

    ##########################################
    #
    #  Version Styles:
    #    semantic, public, pep440, git
    #
    ##########################################

    @property
    def semantic(self):
        """
        This is the standard semantic version format.  For most
        purposes this is the best choice.
        """
        v = f"{self._major}.{self._minor}.{self._patch}"
        if self._prerelease:
            v = f"{v}-{self._prerelease}"
        if self._build:
            v = f"{v}+{self._build}"
        return v

    @property
    def pep440(self):
        """
        This is a loose translation to pep440 compliant.  They
        allow more than 3 segments of ints, so we can do
        1.2.3.899b2 where 899 is build # and b2 is prerelease
        """
        base = self.public
        prerelease = ""
        build = ""

        if self.prerelease:
            numeric = self.prerelease_int
            if numeric is None:
                prerelease = ""
            elif "alpha" in self.prerelease.lower():
                prerelease = f"a{numeric}"
            elif "beta" in self.prerelease.lower():
                prerelease = f"b{numeric}"
            elif "rc" in self.prerelease.lower():
                prerelease = f"rc{numeric}"
            else:
                prerelease = f".dev{numeric}"

        if self.build:
            build = f".{self.build_int}"

        v = f"{base}{prerelease}{build}"
        return v

    @property
    def public(self):
        """
        Public Version - Something simple for pypi
        Should be PEP440, but looks like they take plain
        and simple semantic versions.
        """

        return f"{self._major}.{self._minor}.{self._patch}"

    @property
    def git(self):
        """
        This is a git formatted version, made up from metadata
        retrieved with `git describe`.

        format will be: M.m.p-dev.<distance>+build.<commit_sha>
        ex: 4.2.0-rc.3.dev.5+fcf2c8fd
        """
        if self._git_metadata is None:
            return "GIT METADATA NOT AVAILABLE"

        tag = self._git_metadata.tag
        dirty = self._git_metadata.dirty
        commit_sha = self._git_metadata.commit_sha
        distance = self._git_metadata.distance

        # Add distance in prerelease. Check for existing prerelease
        if distance and self.prerelease:
            pre = f"-{self.prerelease}.dev.{distance}"
        elif distance:
            pre = f"-dev.{distance}"
        elif dirty:
            pre = "-dev.DIRTY"
        else:
            pre = ""

        # Construct build metadata with git sha + tracked build
        if commit_sha:
            build = f"{commit_sha}.{self.build_int}"
        else:
            build = f"build.{self.build_int}"

        # Add build metadata to version
        v = f"{tag}{pre}+{build}"
        return v

    ##########################################
    #
    #  Descriptors: original, new_release
    #
    ##########################################

    @property
    def bumped(self):
        """Use this property to determine if a version instance
        has already been bumped or not.  Initially on creation a
        version.bumped will be False.  Aftter a .bump() it will
        return True.
        """
        if self._frozen.part:
            return True
        return False

    @property
    def original(self):
        """Use the data stored in _frozen to return a Version instance
        of the original datac, in case a bump has been made and some
        type of comparison is desired.

        _frozen.part: the part of the original version that was
        bumped.  Will be None until a bump occurs.
        """
        return Version.parse(self._frozen.semantic)

    @property
    def age(self):
        part = self._frozen.part
        if part in ["major", "minor", "patch", "prerelease"]:
            return "new"
        elif part in ["build"]:
            return "rebuild"
        else:
            return "unknown"

    @property
    def env(self):
        if self._prerelease:
            return "development"
        return "production"

    @property
    def tag(self):
        return f"v{self.public}"

    #########################
    #
    #  Version methods
    #
    #########################

    def is_canonical(self):
        return Version.pep440_re.match(self.pep440) is not None

    def set_prerelease_token(self, token):
        self._prerelease = f"{token}.0"

    def bump(self, part=None, pre=None):
        """
        Exposed bump method in the public api.
        Arguments:
            part: Which part of the semantic version to bump.
            Still valid if blank because the tracked build
            number will be incremented.
        """
        part = part.lower()

        if part not in Version.BUMPABLE:
            raise ValueError(f"{part} is not bumpable")

        # additional arg for setting prerelease
        if pre:
            self.set_prerelease_token(pre)

        # Record the bumped part
        self._frozen.part = part
        # Always increment the build number
        self.increment_build()

        # Find the part-specifric bump function
        bump_method = getattr(self, f"bump_{part}")
        bump_method()

    def bump_major(self):
        """
        Bump method for bumping MAJOR
        """

        self._major = self._major + 1
        self._minor = 0
        self._patch = 0
        self._prerelease = None

    def bump_minor(self):
        """
        Bump method for bumping MINOR
        """

        self._minor = self._minor + 1
        self._patch = 0
        self._prerelease = None

    def bump_patch(self):
        """
        Bump method for bumping PATCH
        """

        self._patch = self._patch + 1
        self._prerelease = None

    def bump_prerelease(self):
        """
        Bump method for bumping PRERELEASE
        """

        prerelease = Version.increment_string(
            self._prerelease or Version.DEFAULT_PRERELEASE
        )
        self._prerelease = prerelease

    def bump_build(self):
        """ """
        pass

    def increment_build(self):
        """
        Always increment build number
        """

        build = Version.increment_string(self._build or Version.DEFAULT_BUILD)
        self._build = build

    @classmethod
    def increment_string(cls, string):
        """
        Look for the last sequence of number(s) in a string and increment.
        arguments:
            string: the string to search for.
        returns: the incremented string
        Source:
        http://code.activestate.com/recipes/442460-increment-numbers-in-a-string/#c1
        """

        match = cls.last_number_re.search(string)
        if match:
            next_ = str(int(match.group(1)) + 1)
            start, end = match.span(1)
            string = string[: max(end - len(next_), start)] + next_ + string[end:]
        return string

    @classmethod
    def parse(cls, version):
        """
        Parse version string to a Version instance.
        """

        match = cls.semver_re.match(version)
        if match is None:
            raise ValueError(f"{version} is not valid semantic version string")

        matched_parts = match.groupdict()
        return cls(**matched_parts)
