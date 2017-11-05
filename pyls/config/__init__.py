# Copyright 2017 Palantir Technologies, Inc.
from configparser import RawConfigParser
import logging
import os
import pluggy

from .. import hookspecs, uris, PYLS
from .flake8_conf import Flake8Config
from .pycodestyle_conf import PyCodeStyleConfig


log = logging.getLogger(__name__)

# Sources of config, first source overrides next source
DEFAULT_CONFIG_SOURCES = ['pycodestyle', 'flake8']


class Config(object):

    def __init__(self, root_uri, init_opts):
        self._root_path = uris.to_fs_path(root_uri)
        self._root_uri = root_uri
        self._init_opts = init_opts

        self._disabled_plugins = []
        self._settings = {}

        self._config_sources = {
            'flake8': Flake8Config(self._root_path),
            'pycodestyle': PyCodeStyleConfig(self._root_path)
        }

        self._pm = pluggy.PluginManager(PYLS)
        self._pm.trace.root.setwriter(log.debug)
        self._pm.enable_tracing()
        self._pm.add_hookspecs(hookspecs)
        self._pm.load_setuptools_entrypoints(PYLS)

        for name, plugin in self._pm.list_name_plugin():
            log.info("Loaded pyls plugin %s from %s", name, plugin)

        for plugin_conf in self._pm.hook.pyls_settings(config=self):
            self.update(plugin_conf)

    @property
    def disabled_plugins(self):
        return self._disabled_plugins

    @property
    def plugin_manager(self):
        return self._pm

    @property
    def init_opts(self):
        return self._init_opts

    @property
    def root_uri(self):
        return self._root_uri

    @property
    def settings(self):
        return self._settings

    def find_parents(self, path, names):
        root_path = uris.to_fs_path(self._root_uri)
        return find_parents(root_path, path, names)

    def plugin_settings(self, plugin, doc_path=None):
        # Project settings > Language server settings > User settings
        config = {}
        sources = self._settings.get('configSources', DEFAULT_CONFIG_SOURCES)

        for source_name in reversed(sources):
            source = self._config_sources[source_name]
            source_conf = source.user_config()
            log.debug("Got user config from %s: %s", source.__class__.__name__, source_conf)
            config = _merge_dicts(config, source_conf)
        log.debug("With user configuration: %s", config)

        config = _merge_dicts(config, self._settings)
        log.debug("With pyls configuration: %s", config)

        for source_name in reversed(sources):
            source = self._config_sources[source_name]
            source_conf = source.project_config(path=doc_path)
            log.debug("Got project config from %s: %s", source.__class__.__name__, source_conf)
            config = _merge_dicts(config, source_conf)
        log.debug("With project configuration: %s", config)

        return config.get('plugins', {}).get(plugin, {})

    def update(self, settings):
        """Recursively merge the given settings into the current settings."""
        self._settings = _merge_dicts(self._settings, settings)
        log.info("Updated settings to %s", self._settings)

        # All plugins default to enabled
        self._disabled_plugins = [
            plugin for name, plugin in self.plugin_manager.list_name_plugin()
            if not self._settings.get('plugins', {}).get(name, {}).get('enabled', True)
        ]
        log.info("Disabled plugins: %s", self._disabled_plugins)


def build_config(key, config_files):
    """Parse configuration from the given files for the given key."""
    config = RawConfigParser()

    if not config_files:
        # If no config files match, we can't do much
        return {}

    # Find out which section header is used, pep8 or pycodestyle
    files_read = config.read(config_files)
    log.debug("Loaded configuration from %s", files_read)

    if config.has_section(key):
        return {k: v for k, v in config.items(key)}

    return {}


def find_parents(root, path, names):
    """Find files matching the given names relative to the given path.

    Args:
        path (str): The file path to start searching up from.
        names (List[str]): The file/directory names to look for.
        root (str): The directory at which to stop recursing upwards.

    Note:
        The path MUST be within the root.
    """
    if not root:
        return []

    if not os.path.commonprefix((root, path)):
        log.warning("Path %s not in %s", path, root)
        return []

    # Split the relative by directory, generate all the parent directories, then check each of them.
    # This avoids running a loop that has different base-cases for unix/windows
    # e.g. /a/b and /a/b/c/d/e.py -> ['/a/b', 'c', 'd']
    dirs = [root] + os.path.relpath(os.path.dirname(path), root).split(os.path.sep)

    # Search each of /a/b/c, /a/b, /a
    while dirs:
        search_dir = os.path.join(*dirs)
        existing = list(filter(os.path.exists, [os.path.join(search_dir, n) for n in names]))
        if existing:
            return existing
        dirs.pop()

    # Otherwise nothing
    return []


def _merge_dicts(dict_a, dict_b):
    """Recursively merge dictionary b into dictionary a if the value is not None."""
    def _merge_dicts_(a, b):
        for key in set(a.keys()).union(b.keys()):
            if key in a and key in b:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    yield (key, dict(_merge_dicts_(a[key], b[key])))
                elif b[key] is not None:
                    yield (key, b[key])
                else:
                    yield (key, a[key])
            elif key in a:
                yield (key, a[key])
            elif b[key] is not None:
                yield (key, b[key])
    return dict(_merge_dicts_(dict_a, dict_b))
