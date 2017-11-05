# Copyright 2017 Palantir Technologies, Inc.
import configparser
import os
import sys


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

    def project_config(self, document_path):
        """Return project-level (i.e. workspace directory) configuration."""
        raise NotImplementedError()

    def read_config_from_files(self, files):
        # TODO(gatesn): cache based on file modified timestamps
        config = configparser.RawConfigParser()
        found_files = []
        for filename in files:
            found_files.extend(config.read(filename))
        return config
