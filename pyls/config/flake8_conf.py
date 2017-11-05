# Copyright 2017 Palantir Technologies, Inc.
import logging
import os
from .source import ConfigSource
from . import _utils
from pyls._utils import find_parents

log = logging.getLogger(__name__)

CONFIG_KEY = 'flake8'
USER_CONFIGS = ['~\.flake8'] if os.name == 'nt' else ['~/.config/flake8']
PROJECT_CONFIGS = ['.flake8', 'setup.cfg', 'tox.ini']

OPTIONS = [
    ('max-complexity', 'plugins.mccabe.threshold', int),
    ('max-line-length', 'plugins.pycodestyle.maxLineLength', int),
]


class Flake8Config(ConfigSource):
    """Parse flake8 configurations."""

    def user_config(self):
        config_file = self._user_config_file()
        config = self.read_config_from_files([config_file])
        return _utils.parse_config(config, CONFIG_KEY, OPTIONS)

    def _user_config_file(self):
        if self.is_windows:
            return os.path.expanduser('~\\.flake8')
        else:
            return os.path.join(self.xdg_home, 'flake8')

    def project_config(self, path=None):
        if path:
            files = find_parents(self.root_path, path, PROJECT_CONFIGS)
        else:
            files = [os.path.join(self.root_path, filename) for filename in PROJECT_CONFIGS]

        config = self.read_config_from_files(files)
        return _utils.parse_config(config, CONFIG_KEY, OPTIONS)
