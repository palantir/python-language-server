# Copyright 2017 Palantir Technologies, Inc.
import configparser
import logging

log = logging.getLogger(__name__)


def build_config(key, config_files):
    """Parse configuration from the given files for the given key."""
    config = configparser.RawConfigParser()

    if not config_files:
        # If no config files match, we can't do much
        return {}

    # Find out which section header is used, pep8 or pycodestyle
    files_read = config.read(config_files)
    log.debug("Loaded configuration from %s", files_read)

    if config.has_section(key):
        return {k: v for k, v in config.items(key)}

    return {}


def parse_config(config, key, options):
    """Parse the config with the given options."""
    conf = {}
    for source, destination, opt_type in options:
        opt_value = _get_opt(config, key, source, opt_type)
        if opt_value is not None:
            _set_opt(conf, destination, opt_value)
    return conf


def _get_opt(config, key, option, opt_type):
    """Get an option from a configparser with the given type."""
    for opt_key in [option, option.replace('-', '_')]:
        if not config.has_option(key, opt_key):
            continue

        if opt_type == bool:
            return config.getbool(key, opt_key)

        if opt_type == int:
            return config.getint(key, opt_key)

        if opt_type == str:
            return config.get(key, opt_key)

        if opt_type == list:
            return _parse_list_opt(config.get(key, opt_key))

        raise ValueError("Unknown option type: %s", opt_type)


def _parse_list_opt(string):
    return [s.strip() for s in string.split(",") if s.strip()]


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
