# Copyright 2019 Palantir Technologies, Inc.
import logging
import os
from pyls._utils import find_parents
from .source import ConfigSource, _get_opt, _set_opt

log = logging.getLogger(__name__)

PROJECT_CONFIGS = ['.pylintrc', 'pylintrc']

CONFIG_KEYS = { # 'option': 'section key'
    'disable': 'MESSAGES CONTROL',
    'ignore': 'MASTER',
    'max-line-length': 'FORMAT',
}

OPTIONS = [
    ('disable', 'plugins.pylint.disable', list),
    ('ignore', 'plugins.pylint.ignore', list),
    ('max-line-length', 'plugins.pylint.maxLineLength', int),
]


class PylintConfig(ConfigSource):
    """Parse pylint configurations."""

    def user_config(self):
        config_file = self._user_config_file()
        config = self.read_config_from_files([config_file])
        return self.parse_config(config, CONFIG_KEYS, OPTIONS)

    def _user_config_file(self):
        if self.is_windows:
            return os.path.expanduser('~\\.pylintrc')
        return os.path.expanduser('~/.pylintrc')

    def project_config(self, document_path):
        files = find_parents(self.root_path, document_path, PROJECT_CONFIGS)
        config = self.read_config_from_files(files)
        return self.parse_config(config, CONFIG_KEYS, OPTIONS)

    @staticmethod
    def parse_config(config, keys, options):
        """Parse the config with the given options.
        This method override its parent to use multiple keys depending
        on the value we want to get.
        """
        conf = {}
        for source, destination, opt_type in options:
            key = keys[source]
            opt_value = _get_opt(config, key, source, opt_type)
            if opt_value is not None:
                _set_opt(conf, destination, opt_value)
        return conf
