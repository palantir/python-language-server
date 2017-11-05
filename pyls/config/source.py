# Copyright 2017 Palantir Technologies, Inc.
import configparser
import logging
import os
import sys

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
        return {}

    def project_config(self, path=None):
        """Return project-level (i.e. workspace directory) configuration."""
        return {}


def read_config(files):
    config = configparser.RawConfigParser()
    found_files = []
    for filename in files:
        found_files.extend(config.read(filename))
    return config


def parse_config(config, key, options):
    """Parse the config with the given options."""
    conf = {}
    for source, destination, opt_type in options:
        opt_value = _get_opt(config, key, source, opt_type)
        _set_opt(conf, destination, opt_value)
    return conf


def _get_opt(config, key, option, opt_type):
    """Get an option from a configparser with the given type."""
    for opt_key in [option, option.replace('-', '_')]:
        if not config.has_option(key, opt_key):
            continue

        if opt_type == int:
            return config.getint(key, opt_key)

        return config.get(key, opt_key)


def _set_opt(config_dict, path, value):
    """Set the value in the dictionary at the given path if the value is not None."""
    if value is None:
        return

    if '.' not in path:
        config_dict[path] = value
        return

    key, rest = path.split(".", 1)
    if key not in config_dict:
        config_dict[key] = {}

    _set_opt(config_dict[key], rest, value)
