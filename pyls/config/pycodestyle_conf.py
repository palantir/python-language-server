# Copyright 2017 Palantir Technologies, Inc.
import os
import pycodestyle
from .source import ConfigSource, parse_config


CONFIG_KEY = 'pycodestyle'
USER_CONFIGS = [pycodestyle.USER_CONFIG] if pycodestyle.USER_CONFIG else []
PROJECT_CONFIGS = ['pycodestyle.cfg', 'setup.cfg', 'tox.ini']

OPTIONS = [
    ('max-line-length', 'plugins.pycodestyle.maxLineLength', int),
]


class PyCodeStyleConfig(ConfigSource):

    def user_config(self):
        config_file = self._user_config_file()
        config = self.read_config_from_files([config_file])
        return parse_config(config, CONFIG_KEY, OPTIONS)

    def _user_config_file(self):
        if self.is_windows:
            return os.path.expanduser('~\\.pycodestyle')
        else:
            return os.path.join(self.xdg_home, 'pycodestyle')

    def project_config(self, path=None):
        return {}
