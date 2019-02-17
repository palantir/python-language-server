# Copyright 2017 Palantir Technologies, Inc.
import io
import logging
import os
import re
import subprocess


from pyls import hookimpl, uris
from pyls.lsp import SymbolKind

log = logging.getLogger(__name__)

DEFAULT_TAG_FILE = "${workspaceFolder}/.vscode/tags"
DEFAULT_CTAGS_EXE = "ctags"

TAG_RE = re.compile((
    r'(?P<name>\w+)\t'
    r'(?P<file>.*)\t'
    r'/\^(?P<code>.*)\$/;"\t'
    r'kind:(?P<type>\w+)\t'
    r'line:(?P<line>\d+)$'
))

CTAG_OPTIONS = [
    "--tag-relative=yes",
    "--exclude=.git",
    "--exclude=env",
    "--exclude=log",
    "--exclude=tmp",
    "--exclude=doc",
    "--exclude=deps",
    "--exclude=node_modules",
    "--exclude=.vscode",
    "--exclude=public/assets",
    "--exclude=*.git*",
    "--exclude=*.pyc",
    "--exclude=*.pyo",
    "--exclude=.DS_Store",
    "--exclude=**/*.jar",
    "--exclude=**/*.class",
    "--exclude=**/.idea/",
    "--exclude=build",
    "--exclude=Builds",
    "--exclude=doc",
    "--fields=Knz",
    "--extra=+f",
]

CTAG_SYMBOL_MAPPING = {
    "array": SymbolKind.Array,
    "boolean": SymbolKind.Boolean,
    "class": SymbolKind.Class,
    "classes": SymbolKind.Class,
    "constant": SymbolKind.Constant,
    "constants": SymbolKind.Constant,
    "constructor": SymbolKind.Constructor,
    "enum": SymbolKind.Enum,
    "enums": SymbolKind.Enum,
    "enumeration": SymbolKind.Enum,
    "enumerations": SymbolKind.Enum,
    "field": SymbolKind.Field,
    "fields": SymbolKind.Field,
    "file": SymbolKind.File,
    "files": SymbolKind.File,
    "function": SymbolKind.Function,
    "functions": SymbolKind.Function,
    "member": SymbolKind.Function,
    "interface": SymbolKind.Interface,
    "interfaces": SymbolKind.Interface,
    "key": SymbolKind.Key,
    "keys": SymbolKind.Key,
    "method": SymbolKind.Method,
    "methods": SymbolKind.Method,
    "module": SymbolKind.Module,
    "modules": SymbolKind.Module,
    "namespace": SymbolKind.Namespace,
    "namespaces": SymbolKind.Namespace,
    "number": SymbolKind.Number,
    "numbers": SymbolKind.Number,
    "null": SymbolKind.Null,
    "object": SymbolKind.Object,
    "package": SymbolKind.Package,
    "packages": SymbolKind.Package,
    "property": SymbolKind.Property,
    "properties": SymbolKind.Property,
    "objects": SymbolKind.Object,
    "string": SymbolKind.String,
    "variable": SymbolKind.Variable,
    "variables": SymbolKind.Variable,
    "projects": SymbolKind.Package,
    "defines": SymbolKind.Module,
    "labels": SymbolKind.Interface,
    "macros": SymbolKind.Function,
    "types (structs and records)": SymbolKind.Class,
    "subroutine": SymbolKind.Method,
    "subroutines": SymbolKind.Method,
    "types": SymbolKind.Class,
    "programs": SymbolKind.Class,
    "Object\'s method": SymbolKind.Method,
    "Module or functor": SymbolKind.Module,
    "Global variable": SymbolKind.Variable,
    "Type name": SymbolKind.Class,
    "A function": SymbolKind.Function,
    "A constructor": SymbolKind.Constructor,
    "An exception": SymbolKind.Class,
    "A \'structure\' field": SymbolKind.Field,
    "procedure": SymbolKind.Function,
    "procedures": SymbolKind.Function,
    "constant definitions": SymbolKind.Constant,
    "javascript functions": SymbolKind.Function,
    "singleton methods": SymbolKind.Method,
}


class CtagMode(object):
    NONE = "none"
    APPEND = "append"
    REBUILD = "rebuild"


DEFAULT_ON_START_MODE = CtagMode.REBUILD
DEFAULT_ON_SAVE_MODE = CtagMode.APPEND


class CtagsPlugin(object):

    def __init__(self):
        self._started = False
        self._workspace = None

    @hookimpl
    def pyls_document_did_open(self, config, workspace):
        """Since initial settings are sent after initialization, we use didOpen as the hook instead."""
        if self._started:
            return
        self._started = True
        self._workspace = workspace

        settings = config.plugin_settings('ctags')
        ctags_exe = _ctags_exe(settings)

        for tag_file in settings.get('tagFiles', []):
            mode = tag_file.get('onStart', DEFAULT_ON_START_MODE)

            if mode == CtagMode.NONE:
                log.debug("Skipping tag file with onStart mode NONE: %s", tag_file)
                continue

            tag_file_path = self._format_path(tag_file['filePath'])
            tags_dir = self._format_path(tag_file['directory'])

            execute(ctags_exe, tag_file_path, tags_dir, mode == CtagMode.APPEND)

    @hookimpl
    def pyls_document_did_save(self, config, document):
        settings = config.plugin_settings('ctags')
        ctags_exe = _ctags_exe(settings)

        for tag_file in settings.get('tagFiles', []):
            mode = tag_file.get('onSave', DEFAULT_ON_SAVE_MODE)

            if mode == CtagMode.NONE:
                log.debug("Skipping tag file with onSave mode NONE: %s", tag_file)
                continue

            tag_file_path = self._format_path(tag_file['filePath'])
            tags_dir = self._format_path(tag_file['directory'])

            if not os.path.normpath(document.path).startswith(os.path.normpath(tags_dir)):
                log.debug("Skipping onSave tag generation since %s is not in %s", tag_file_path, tags_dir)
                continue

            execute(ctags_exe, tag_file_path, tags_dir, mode == CtagMode.APPEND)

    @hookimpl
    def pyls_workspace_symbols(self, config, query):
        settings = config.plugin_settings('ctags')

        symbols = []
        for tag_file in settings.get('tagFiles', []):
            symbols.extend(parse_tags(self._format_path(tag_file['filePath']), query))

        return symbols

    def _format_path(self, path):
        return path.format(**{"workspaceRoot": self._workspace.root_path})


def _ctags_exe(settings):
    # TODO(gatesn): verify ctags is installed and right version
    return settings.get('ctagsPath', DEFAULT_CTAGS_EXE)


def execute(ctags_exe, tag_file, directory, append=False):
    """Run ctags against the given directory."""
    # Ensure the directory exists
    tag_file_dir = os.path.dirname(tag_file)
    if not os.path.exists(tag_file_dir):
        os.makedirs(tag_file_dir)

    cmd = [ctags_exe, '-f', tag_file, '--languages=Python', '-R'] + CTAG_OPTIONS
    if append:
        cmd.append('--append')
    cmd.append(directory)

    log.info("Executing exuberant ctags: %s", cmd)
    log.info("ctags: %s", subprocess.check_output(cmd))


def parse_tags(tag_file, query):
    if not os.path.exists(tag_file):
        return

    with io.open(tag_file, 'rb') as f:
        for line in f:
            tag = parse_tag(line.decode('utf-8', errors='ignore'), query)
            if tag:
                yield tag


def parse_tag(line, query):
    match = TAG_RE.match(line)
    log.info("Got match %s from line: %s", match, line)
    log.info("Line: ", line.replace('\t', '\\t').replace(' ', '\\s'))

    if not match:
        return None

    name = match.group('name')

    # TODO(gatesn): Support a fuzzy match, but for now do a naive substring match
    if query.lower() not in name.lower():
        return None

    line = int(match.group('line')) - 1

    return {
        'name': name,
        'kind': CTAG_SYMBOL_MAPPING.get(match.group('type'), SymbolKind.Null),
        'location': {
            'uri': uris.from_fs_path(match.group('file')),
            'range': {
                'start': {'line': line, 'character': 0},
                'end': {'line': line, 'character': 0}
            }
        }
    }


INSTANCE = CtagsPlugin()
