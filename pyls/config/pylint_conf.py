# Copyright 2017 Palantir Technologies, Inc.
import logging
import os
from pyls._utils import find_parents
from .source import ConfigSource

log = logging.getLogger(__name__)

PROJECT_CONFIGS = ['.pylintrc', 'pylintrc']
RCFILE_CONFIG = 'plugins.pylint.rcfile'


class PylintConfig(ConfigSource):
    """Parse pylint configurations."""

    def user_config(self):
        config_file = self._user_config_file()
        return {RCFILE_CONFIG: config_file}

    def _user_config_file(self):
        if self.is_windows:
            return os.path.expanduser('~\\.pylintrc')
        return os.path.join(self.xdg_home, '.pylintrc')

    def project_config(self, document_path):
        files = find_parents(self.root_path, document_path, PROJECT_CONFIGS)
        if files:
            return {RCFILE_CONFIG: files[0]}
        return {}
