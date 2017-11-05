# Copyright 2017 Palantir Technologies, Inc.
import os
import pycodestyle
from .source import ConfigSource
from . import _utils
from pyls._utils import find_parents


CONFIG_KEY = 'pycodestyle'
USER_CONFIGS = [pycodestyle.USER_CONFIG] if pycodestyle.USER_CONFIG else []
PROJECT_CONFIGS = ['pycodestyle.cfg', 'setup.cfg', 'tox.ini']

OPTIONS = [
    ('exclude', 'plugins.pycodestyle.exclude', list),
    ('filename', 'plugins.pycodestyle.filename', list),
    ('hang_closing', 'plugins.pycodestyle.hangClosing', bool),
    ('ignore', 'plugins.pycodestyle.ignore', list),
    ('max-line-length', 'plugins.pycodestyle.maxLineLength', int),
    ('select', 'plugins.pycodestyle.select', list),
]


class PyCodeStyleConfig(ConfigSource):

    def user_config(self):
        config_file = self._user_config_file()
        config = self.read_config_from_files([config_file])
        return _utils.parse_config(config, CONFIG_KEY, OPTIONS)

    def _user_config_file(self):
        if self.is_windows:
            return os.path.expanduser('~\\.pycodestyle')
        else:
            return os.path.join(self.xdg_home, 'pycodestyle')

    def project_config(self, path=None):
        if path:
            files = find_parents(self.root_path, path, PROJECT_CONFIGS)
        else:
            files = [os.path.join(self.root_path, filename) for filename in PROJECT_CONFIGS]

        config = self.read_config_from_files(files)
        return _utils.parse_config(config, CONFIG_KEY, OPTIONS)