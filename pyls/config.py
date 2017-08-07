# Copyright 2017 Palantir Technologies, Inc.
from configparser import RawConfigParser
import logging
import os
import pluggy
from urllib.parse import urlparse, unquote

from . import hookspecs, PYLS

log = logging.getLogger(__name__)


class Config(object):

    def __init__(self, root_uri, init_opts):
        self._root_uri = root_uri
        self._init_opts = init_opts

        self._pm = pluggy.PluginManager(PYLS)
        self._pm.trace.root.setwriter(log.debug)
        self._pm.enable_tracing()
        self._pm.add_hookspecs(hookspecs)
        self._pm.load_setuptools_entrypoints(PYLS)

    @property
    def plugin_manager(self):
        return self._pm

    @property
    def init_opts(self):
        return self._init_opts

    @property
    def root_uri(self):
        return self._root_uri

    def find_parents(self, path, names):
        root_path = unquote(urlparse(self._root_uri).path)
        return find_parents(root_path, path, names)


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
        path (str): The path to start searching up from
        names (List[str]): The file/directory names to look for
        root (str): The directory at which to stop recursing upwards.

    Note:
        The path MUST be within the root.
    """
    if not root:
        return []
    if not os.path.commonprefix((root, path)):
        log.warning("Path %s not in %s", path, root)
        return []

    curdir = os.path.dirname(path)

    while curdir != os.path.dirname(root) and curdir != '/':
        existing = list(filter(os.path.exists, [os.path.join(curdir, n) for n in names]))
        if existing:
            return existing
        curdir = os.path.dirname(curdir)
