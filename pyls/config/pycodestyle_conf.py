# Copyright 2017 Palantir Technologies, Inc.
import pycodestyle
from .source import ConfigSource


USER_CONFIGS = [pycodestyle.USER_CONFIG] if pycodestyle.USER_CONFIG else []
PROJECT_CONFIGS = ['pycodestyle.cfg', 'setup.cfg', 'pep8.cfg', 'tox.ini']


class PyCodeStyleConfig(ConfigSource):

    def user_config(self):
        return {}

    def project_config(self, path=None):
        return {}
