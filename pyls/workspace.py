# Copyright 2017 Palantir Technologies, Inc.
import io
import logging
import os
import re
import sys
import imp
import pkgutil

import jedi
from rope.base import libutils
from rope.base.project import Project

from . import lsp, uris, _utils

log = logging.getLogger(__name__)

# TODO: this is not the best e.g. we capture numbers
RE_START_WORD = re.compile('[A-Za-z_0-9]*$')
RE_END_WORD = re.compile('^[A-Za-z_0-9]*')


def get_submodules(mod):
    """Get all submodules of a given module"""
    def catch_exceptions(_module):
        pass

    try:
        m = __import__(mod)
        submodules = [mod]
        submods = pkgutil.walk_packages(m.__path__, m.__name__ + '.', catch_exceptions)
        for sm in submods:
            sm_name = sm[1]
            submodules.append(sm_name)
    except ImportError:
        return []
    except:  # pylint: disable=bare-except
        return [mod]
    return submodules


def get_preferred_submodules():
    mods = ['numpy', 'scipy', 'sympy', 'pandas',
            'networkx', 'statsmodels', 'matplotlib', 'sklearn',
            'skimage', 'mpmath', 'os', 'PIL',
            'OpenGL', 'array', 'audioop', 'binascii', 'cPickle',
            'cStringIO', 'cmath', 'collections', 'datetime',
            'errno', 'exceptions', 'gc', 'imageop', 'imp',
            'itertools', 'marshal', 'math', 'mmap', 'msvcrt',
            'nt', 'operator', 'parser', 'rgbimg', 'signal',
            'strop', 'sys', 'thread', 'time', 'wx', 'xxsubtype',
            'zipimport', 'zlib', 'nose', 'os.path']

    submodules = []
    for mod in mods:
        submods = get_submodules(mod)
        submodules += submods

    actual = []
    for submod in submodules:
        try:
            imp.find_module(submod)
            actual.append(submod)
        except ImportError:
            pass

    return actual


class Workspace(object):

    M_PUBLISH_DIAGNOSTICS = 'textDocument/publishDiagnostics'
    M_APPLY_EDIT = 'workspace/applyEdit'
    M_SHOW_MESSAGE = 'window/showMessage'
    PRELOADED_MODULES = get_preferred_submodules()

    def __init__(self, root_uri, rpc_manager):
        self._root_uri = root_uri
        self._rpc_manager = rpc_manager
        self._root_uri_scheme = uris.urlparse(self._root_uri)[0]
        self._root_path = uris.to_fs_path(self._root_uri)
        self._docs = {}

        # Whilst incubating, keep private
        self.__rope = Project(self._root_path)
        self.__rope.prefs.set('extension_modules', self.PRELOADED_MODULES)

    @property
    def _rope(self):
        # TODO: we could keep track of dirty files and validate only those
        self.__rope.validate()
        return self.__rope

    @property
    def documents(self):
        return self._docs

    @property
    def root_path(self):
        return self._root_path

    @property
    def root_uri(self):
        return self._root_uri

    def is_local(self):
        return (self._root_uri_scheme == '' or self._root_uri_scheme == 'file') and os.path.exists(self._root_path)

    def get_document(self, doc_uri):
        return self._docs[doc_uri]

    def put_document(self, doc_uri, content, version=None):
        path = uris.to_fs_path(doc_uri)
        self._docs[doc_uri] = Document(
            doc_uri, content,
            extra_sys_path=self.source_roots(path), version=version, rope=self._rope
        )

    def rm_document(self, doc_uri):
        self._docs.pop(doc_uri)

    def update_document(self, doc_uri, change, version=None):
        self._docs[doc_uri].apply_change(change)
        self._docs[doc_uri].version = version

    def apply_edit(self, edit, on_result=None, on_error=None):
        return self._rpc_manager.call(
            self.M_APPLY_EDIT, {'edit': edit},
            on_result=on_result, on_error=on_error
        )

    def publish_diagnostics(self, doc_uri, diagnostics):
        self._rpc_manager.notify(self.M_PUBLISH_DIAGNOSTICS, params={'uri': doc_uri, 'diagnostics': diagnostics})

    def show_message(self, message, msg_type=lsp.MessageType.Info):
        self._rpc_manager.notify(self.M_SHOW_MESSAGE, params={'type': msg_type, 'message': message})

    def source_roots(self, document_path):
        """Return the source roots for the given document."""
        files = _utils.find_parents(self._root_path, document_path, ['setup.py']) or []
        return [os.path.dirname(setup_py) for setup_py in files]


class Document(object):

    def __init__(self, uri, source=None, version=None, local=True, extra_sys_path=None, rope=None):
        self.uri = uri
        self.version = version
        self.path = uris.to_fs_path(uri)
        self.filename = os.path.basename(self.path)

        self._local = local
        self._source = source
        self._extra_sys_path = extra_sys_path or []
        self._rope_project = rope

    def __str__(self):
        return str(self.uri)

    @property
    def _rope(self):
        return libutils.path_to_resource(self._rope_project, self.path)

    @property
    def lines(self):
        return self.source.splitlines(True)

    @property
    def source(self):
        if self._source is None:
            with open(self.path, 'r') as f:
                return f.read()
        return self._source

    def apply_change(self, change):
        """Apply a change to the document."""
        text = change['text']
        change_range = change.get('range')

        if not change_range:
            # The whole file has changed
            self._source = text
            return

        start_line = change_range['start']['line']
        start_col = change_range['start']['character']
        end_line = change_range['end']['line']
        end_col = change_range['end']['character']

        # Check for an edit occuring at the very end of the file
        if start_line == len(self.lines):
            self._source = self.source + text
            return

        new = io.StringIO()

        # Iterate over the existing document until we hit the edit range,
        # at which point we write the new text, then loop until we hit
        # the end of the range and continue writing.
        for i, line in enumerate(self.lines):
            if i < start_line:
                new.write(line)
                continue

            if i > end_line:
                new.write(line)
                continue

            if i == start_line:
                new.write(line[:start_col])
                new.write(text)

            if i == end_line:
                new.write(line[end_col:])

        self._source = new.getvalue()

    def offset_at_position(self, position):
        """Return the byte-offset pointed at by the given position."""
        return position['character'] + len(''.join(self.lines[:position['line']]))

    def word_at_position(self, position):
        """Get the word under the cursor returning the start and end positions."""
        if position['line'] >= len(self.lines):
            return ''

        line = self.lines[position['line']]
        i = position['character']
        # Split word in two
        start = line[:i]
        end = line[i:]

        # Take end of start and start of end to find word
        # These are guaranteed to match, even if they match the empty string
        m_start = RE_START_WORD.findall(start)
        m_end = RE_END_WORD.findall(end)

        return m_start[0] + m_end[-1]

    def jedi_names(self, all_scopes=False, definitions=True, references=False):
        return jedi.api.names(
            source=self.source, path=self.path, all_scopes=all_scopes,
            definitions=definitions, references=references
        )

    def jedi_script(self, position=None):
        kwargs = {
            'source': self.source,
            'path': self.path,
            'sys_path': self.sys_path()
        }
        if position:
            kwargs['line'] = position['line'] + 1
            kwargs['column'] = _utils.clip_column(position['character'], self.lines, position['line'])
        return jedi.Script(**kwargs)

    def sys_path(self):
        # Copy our extra sys path
        path = list(self._extra_sys_path)

        # Check to see if we're in a virtualenv
        if 'VIRTUAL_ENV' in os.environ:
            log.info("Using virtualenv %s", os.environ['VIRTUAL_ENV'])
            path.extend(jedi.evaluate.sys_path.get_venv_path(os.environ['VIRTUAL_ENV']))
        else:
            path.extend(sys.path)

        return path
