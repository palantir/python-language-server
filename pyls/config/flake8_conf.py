# Copyright 2017 Palantir Technologies, Inc.
import logging
import os
from .source import ConfigSource, read_config, parse_config

log = logging.getLogger(__name__)

CONFIG_KEY = 'flake8'
USER_CONFIGS = ['~\.flake8'] if os.name == 'nt' else ['~/.config/flake8']
PROJECT_CONFIGS = ['.flake8', 'setup.cfg', 'tox.ini']

OPTIONS = [
    ('max-complexity', 'plugins.mccabe.threshold', int)
]


class Flake8Config(ConfigSource):
    """Parse flake8 configurations.
    We don't want to take a dependency on Flake8, so we manually parse the config.
    """

    def user_config(self):
        config_file = self._user_config_file()
        config = read_config([config_file])
        return parse_config(config, CONFIG_KEY, OPTIONS)

    def _user_config_file(self):
        if self.is_windows:
            return os.path.expanduser('~\\.flake8')
        else:
            return os.path.join(self.xdg_home, 'flake8')

    def project_config(self, path=None):
        # FIXME: this isn't in root_path, this is relative to the file...
        config_files = [os.path.join(self.root_path, filename) for filename in PROJECT_CONFIGS]
        config = read_config(config_files)
        return parse_config(config, CONFIG_KEY, OPTIONS)
