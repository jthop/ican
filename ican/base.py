# -*- coding: utf-8 -*-
"""
"""


class Registry(object):
    def __init__(self):
        self.reg = {}

    def set(self, name, instance=None):
        if instance is None:
            raise ValueError("Instance cannot be None")
        self.reg[name] = instance

    def get(self, name):
        return self.reg.get(name)


registry = Registry()


class Base:
    def __init__(self):
        pass

    @property
    def version(self):
        return registry.get("version")

    @version.setter
    def version(self, value):
        registry.set("version", value)

    @property
    def config(self):
        return registry.get("config")

    @config.setter
    def config(self, value):
        registry.set("config", value)

    @property
    def git(self):
        return registry.get("git")

    @git.setter
    def git(self, value):
        registry.set("git", value)

    @property
    def ican(self):
        return registry.get("ican")

    @ican.setter
    def ican(self, value):
        registry.set("ican", value)
