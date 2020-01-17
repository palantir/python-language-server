import logging
import os
from pyls._utils import find_parents, get_config_by_path, merge_dicts, normalize_paths
from .source import ConfigSource, _set_opt

log = logging.getLogger(__name__)

CONFIG_KEY = 'pyls'
PROJECT_CONFIGS = ['setup.cfg', 'tox.ini']

OPTIONS = [
    ('source_roots', 'source_roots', list),
]

# list of (config_path, inside_only) tuples for path normalization
NORMALIZED_CONFIGS = [
    ('source_roots', True),
]


class PylsConfig(ConfigSource):
    """Parse pyls configuration"""

    def __init__(self, root_path):
        super(PylsConfig, self).__init__(root_path)

        # If workspace URI has trailing '/', root_path does, too.
        # (e.g. "lsp" on Emacs sends such URI). To avoid normpath at
        # each normalization, os.path.normpath()-ed root_path is
        # cached here.
        self._norm_root_path = os.path.normpath(self.root_path)

    def user_config(self):
        # pyls specific configuration mainly focuses on per-project
        # configuration
        return {}

    def project_config(self, document_path):
        settings = {}
        seen = set()

        # To read config files in root_path even if any config file is
        # found by find_parents() in the directory other than
        # root_path, root_path is listed below as one of targets.
        #
        # On the other hand, "seen" is used to manage name of already
        # evaluated files, in order to avoid multiple evaluation of
        # config files in root_path.
        for target in self.root_path, document_path:
            # os.path.normpath is needed to treat that
            # "root_path/./foobar" and "root_path/foobar" are
            # identical.
            sources = map(os.path.normpath, find_parents(self.root_path, target, PROJECT_CONFIGS))
            files = []
            for source in sources:
                if source not in seen:
                    files.append(source)
                    seen.add(source)
            if not files:
                continue  # there is no file to be read in

            parsed = self.parse_config(self.read_config_from_files(files),
                                       CONFIG_KEY, OPTIONS)
            if not parsed:
                continue  # no pyls specific configuration

            self.normalize(parsed, os.path.dirname(files[0]))

            settings = merge_dicts(settings, parsed)

        return settings

    def normalize(self, config, basedir):
        for config_path, inside_only in NORMALIZED_CONFIGS:
            paths = get_config_by_path(config, config_path)
            if not paths:
                continue  # not specified (or empty)

            normalized = []
            for path, valid in normalize_paths(paths, basedir, inside_only and self._norm_root_path):
                if valid:
                    normalized.append(path)
                else:
                    log.warning("Ignoring path '%s' for pyls.%s", path, config_path)

            _set_opt(config, config_path, normalized)
