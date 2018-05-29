# Copyright 2017 Palantir Technologies, Inc.
from pyls._utils import find_parents
from .source import ConfigSource
import os

CONFIG_KEY = 'jedi'
PROJECT_CONFIGS = ['.jedi']

OPTIONS = [
    ('follow_imports', 'plugins.jedi.follow_imports', bool)
]


class JediConfig(ConfigSource):

    def user_config(self):
        config = self.read_config_from_files([self._user_config_file()])
        return self.parse_config(config, CONFIG_KEY, OPTIONS)

    def _user_config_file(self):
        if self.is_windows:
            return os.path.expanduser('~\\.{}'.format(CONFIG_KEY))
        return os.path.join(self.xdg_home, CONFIG_KEY)

    def project_config(self, document_path):
        files = find_parents(self.root_path, document_path, PROJECT_CONFIGS)
        config = self.read_config_from_files(files)
        return self.parse_config(config, CONFIG_KEY, OPTIONS)
