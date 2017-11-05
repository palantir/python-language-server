# Copyright 2017 Palantir Technologies, Inc.
import configparser
import logging
import os
import sys

from . import _utils

log = logging.getLogger(__name__)


class ConfigSource(object):
    """Base class for implementing a config source."""

    def __init__(self, root_path):
        self.root_path = root_path
        self.is_windows = sys.platform == 'win32'
        self.xdg_home = os.environ.get(
            'XDG_CONFIG_HOME', os.path.expanduser('~/.config')
        )

    def user_config(self):
        """Return user-level (i.e. home directory) configuration."""
        raise NotImplementedError()

    def project_config(self, path=None):
        """Return project-level (i.e. workspace directory) configuration."""
        raise NotImplementedError()

    def find_project_files(self, path, filenames):
        return _utils.find_parents(self.root_path, path, filenames)

    def read_config_from_files(self, files):
        # TODO(gatesn): check if files updated
        config = configparser.RawConfigParser()
        found_files = []
        for filename in files:
            found_files.extend(config.read(filename))
        return config
