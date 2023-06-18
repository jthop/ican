# -*- coding: utf-8 -*-

import re
from .exceptions import VersionNotBumpable
from .log import logger


__version__ = "2.0"


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
    VALID_TOKENS = ["alpha", "beta", "dev", "rc"]
    DEFAULT_TOKEN = "beta"

    semver_re = re.compile(
        r"""
            ^(?P<major>0|[1-9]\d*)
            \.(?P<minor>0|[1-9]\d*)
            \.(?P<patch>0|[1-9]\d*)
            (?:-(?P<token>[0-9a-zA-Z-]+)
            \.(?P<prerelease>0|[1-9]\d*))?
            (?:\+build\.(?P<build>0|[1-9]\d*))?$
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

    def __init__(
        self,
        major=0,
        minor=0,
        patch=0,
        token=DEFAULT_TOKEN,
        prerelease=None,
        build=None
    ):

        self._major = int(major)
        self._minor = int(minor)
        self._patch = int(patch)
        self._token = token
        self._prerelease = prerelease
        self._build = build

        if prerelease:
            self._prerelease = int(prerelease)
        if build:
            self._build = int(build)

        self._git_metadata = None
        self._bumped_part = None
        self._bumped_part_value = None

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

    @property
    def minor(self):
        return self._minor

    @property
    def patch(self):
        return self._patch

    @property
    def prerelease(self):
        if self._prerelease is None:
            return None
        return f"{self._token}.{self._prerelease}"

    @property
    def build(self):
        if self._build is None:
            return None
        return f"build.{self._build}"

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
        if self.prerelease:
            v = f"{v}-{self.prerelease}"
        if self.build:
            v = f"{v}+{self.build}"
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

        if self._prerelease:
            if self._token == "alpha":
                prerelease = f"a{self._prerelease}"
            elif self._token == "beta":
                prerelease = f"b{self._prerelease}"
            elif self._token == "rc":
                prerelease = f"rc{self._prerelease}"
            else:
                prerelease = f".dev{self._prerelease}"

        if self._build:
            build = f".{self._build}"

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
            return None

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
            build = f"{commit_sha}.{self._build}"
        else:
            build = f"build.{self._build}"

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
        if self._bumped_part:
            return True
        return False

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

    def set_token(self, token):
        token = token.lower()
        if self._token != token:
            self._prerelease = 0
            self._token = token
        return

    def bump(self, part="build"):
        """
        Exposed bump method in the public api.
        Arguments:
            part: Which part of the semantic version to bump.
            Still valid if blank because the tracked build
            number will be incremented.
        """

        part = part.lower()
        # "pre" is just shorthand for "prerelease"
        if part == "pre":
            part = "prerelease"
        # shortcut to set the token and bump at same time
        elif part in Version.VALID_TOKENS:
            token = part
            part = "prerelease"
            self.set_token(token)

        if part not in Version.BUMPABLE:
            raise VersionNotBumpable(f"{part} is not bumpable")

        # Record the bumsped part incase we need to rollback
        self._bumped_part = part
        self._bumped_part_value = getattr(self, part)

        # Always increment the build number
        self.increment_build()

        # Find the part-specific bump method
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

        if self._prerelease is None:
            self._prerelease = 0

        self._prerelease += 1

    def bump_build(self):
        """
        This bump_method is included only incase user runs bump build.
        Build has already been bumped since we run increment_build
        separately each bump.
        """
        pass

    def increment_build(self):
        """
        Always increment build number
        """
        if self._build is None:
            self._build = 0

        self._build += 1

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
