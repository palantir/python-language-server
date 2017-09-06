# Copyright 2017 Palantir Technologies, Inc.
import io
import logging
import os
import re
import sys

import jedi

from . import config, lsp, uris

log = logging.getLogger(__name__)

# TODO: this is not the best e.g. we capture numbers
RE_START_WORD = re.compile('[A-Za-z_0-9]*$')
RE_END_WORD = re.compile('^[A-Za-z_0-9]*')


class Workspace(object):

    M_PUBLISH_DIAGNOSTICS = 'textDocument/publishDiagnostics'
    M_APPLY_EDIT = 'workspace/applyEdit'
    M_SHOW_MESSAGE = 'window/showMessage'

    def __init__(self, root_uri, lang_server=None):
        self._root_uri = root_uri
        self._root_uri_scheme = uris.urlparse(self._root_uri)[0]
        self._root_path = uris.to_fs_path(self._root_uri)
        self._docs = {}
        self._lang_server = lang_server

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
            doc_uri, content, sys_path=self.syspath_for_path(path), version=version
        )

    def rm_document(self, doc_uri):
        self._docs.pop(doc_uri)

    def update_document(self, doc_uri, change, version=None):
        self._docs[doc_uri].apply_change(change)
        self._docs[doc_uri].version = version

    def apply_edit(self, edit):
        # Note that lang_server.call currently doesn't return anything
        return self._lang_server.call(self.M_APPLY_EDIT, {'edit': edit})

    def publish_diagnostics(self, doc_uri, diagnostics):
        params = {'uri': doc_uri, 'diagnostics': diagnostics}
        self._lang_server.notify(self.M_PUBLISH_DIAGNOSTICS, params)

    def show_message(self, message, msg_type=lsp.MessageType.Info):
        params = {'type': msg_type, 'message': message}
        self._lang_server.notify(self.M_SHOW_MESSAGE, params)

    def syspath_for_path(self, path):
        """Construct a sensible sys path to use for the given file path.

        Since the workspace root may not be the root of the Python project we instead
        append the closest parent directory containing a setup.py file.
        """
        files = config.find_parents(self._root_path, path, ['setup.py']) or []
        path = [os.path.dirname(setup_py) for setup_py in files]

        # Check to see if we're in a virtualenv
        if 'VIRTUAL_ENV' in os.environ:
            log.info("Using virtualenv %s", os.environ['VIRTUAL_ENV'])
            path.extend(jedi.evaluate.sys_path.get_venv_path(os.environ['VIRTUAL_ENV']))
        else:
            path.extend(sys.path)
        return path


class Document(object):

    def __init__(self, uri, source=None, version=None, local=True, sys_path=None):
        self.uri = uri
        self.version = version
        self.path = uris.to_fs_path(uri)
        self.filename = os.path.basename(self.path)

        self._local = local
        self._source = source
        self._sys_path = sys_path or sys.path

    def __str__(self):
        return str(self.uri)

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

    def word_at_position(self, position):
        """Get the word under the cursor returning the start and end positions."""
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
            'sys_path': self._sys_path
        }
        if position:
            kwargs['line'] = position['line'] + 1
            kwargs['column'] = position['character']
        return jedi.Script(**kwargs)
