# Copyright 2017 Palantir Technologies, Inc.
import logging
import os
from pyls._utils import search
from .source import ConfigSource

log = logging.getLogger(__name__)

PROJECT_CONFIGS = ['.pylintrc', 'pylintrc']
RCFILE_CONFIG = 'plugins.pylint.rcfile'


def set_dict_path(d, path, value):
    current = d
    elems = path.split(".")
    for elem in elems[:-1]:
        if elem not in current.keys():
            current[elem] = {}
        current = current[elem]
    current[elems[-1]] = value
    return d


class PylintConfig(ConfigSource):
    """Parse pylint configurations."""

    def user_config(self):
        config_file = self._user_config_file()
        if os.path.isfile(config_file):
            return set_dict_path({}, RCFILE_CONFIG, config_file)
        return {}

    def _user_config_file(self):
        if self.is_windows:
            return os.path.expanduser('~\\.pylintrc')
        return os.path.join(self.xdg_home, '.pylintrc')

    def project_config(self, document_path):
        log.debug("Searching for config files called %s from %s to %s.",
                  PROJECT_CONFIGS, document_path, self.root_path)
        files = search(self.root_path, PROJECT_CONFIGS)
        log.debug("Found pylint project config files %s.", files)
        if files:
            return set_dict_path({}, RCFILE_CONFIG, files[0])
        return {}
