# -*- coding: utf-8 -*-

from bumpster import version

class TestClass:
    def test_parse(self):
        v = version.Version.parse('1.3.3-beta.2+build.100')
        assert v.version == '1.3.3-beta.2+build.100'

    def test_two(self):
        x = "hello"
        assert hasattr(x, "check")