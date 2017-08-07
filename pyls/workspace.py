# Copyright 2017 Palantir Technologies, Inc.
import io
import logging
import os
import re
import sys
from urllib.parse import urlparse, urlunparse, quote, unquote

import jedi

from . import config, lsp

log = logging.getLogger(__name__)

# TODO: this is not the best e.g. we capture numbers
RE_START_WORD = re.compile('[A-Za-z_0-9]*$')
RE_END_WORD = re.compile('^[A-Za-z_0-9]*')


class Workspace(object):

    M_PUBLISH_DIAGNOSTICS = 'textDocument/publishDiagnostics'
    M_APPLY_EDIT = 'workspace/applyEdit'
    M_SHOW_MESSAGE = 'window/showMessage'

    def __init__(self, root_uri, lang_server=None):
        self._url_parsed = urlparse(root_uri)
        self.root = unquote(self._url_parsed.path)
        self._docs = {}
        self._lang_server = lang_server

    def is_local(self):
        return (self._url_parsed.scheme == '' or self._url_parsed.scheme == 'file') and os.path.exists(self.root)

    def get_document(self, doc_uri):
        return self._docs[doc_uri]

    def put_document(self, doc_uri, content, version=None):
        path = unquote(urlparse(doc_uri).path)
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
        files = config.find_parents(self.root, path, ['setup.py']) or []
        path = [os.path.dirname(setup_py) for setup_py in files]
        path.extend(sys.path)
        return path

    def is_in_workspace(self, path):
        return not self.root or os.path.commonprefix((self.root, path))


class Document(object):

    def __init__(self, uri, source=None, version=None, local=True, sys_path=None):
        self.uri = uri
        self.version = version
        self.path = unquote(urlparse(uri).path)
        self.filename = os.path.basename(self.path)

        self._local = local
        self._source = source
        self._sys_path = sys_path or sys.path

    def __str__(self):
        return str(self.uri)

    @property
    def lines(self):
        # An empty document is much nicer to deal with assuming it has a single
        # line with no characters and no final newline.
        return self.source.splitlines(True) or [u'']

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


def get_uri_like(doc_uri, path):
    """Replace the path in a uri. Little bit hacky!

    Due to https://github.com/PythonCharmers/python-future/issues/273 we have to
    cast all parts to the same type since jedi can return str and urlparse returns
    unicode objects.
    """
    parts = list(urlparse(doc_uri))
    if path[0] != '/' and ':' in path:  # fix path for windows
        drivespec, path = path.split(':', 1)
        path = '/' + drivespec + ':' + quote(path.replace('\\', '/'))
    else:
        path = quote(path)
    parts[2] = path
    return urlunparse([str(p) for p in parts])
