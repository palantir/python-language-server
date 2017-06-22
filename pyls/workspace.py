# Copyright 2017 Palantir Technologies, Inc.
import logging
import os
import re
import sys
from urllib.parse import urlparse, urlunparse

import jedi

log = logging.getLogger(__name__)

# TODO: this is not the best e.g. we capture numbers
RE_START_WORD = re.compile('[A-Za-z_0-9]*$')
RE_END_WORD = re.compile('^[A-Za-z_0-9]*')


class Workspace(object):

    def __init__(self, root):
        self._url_parsed = urlparse(root)
        self.root = self._url_parsed.path
        self._docs = {}

    def is_local(self):
        return (self._url_parsed.scheme == '' or self._url_parsed.scheme == 'file') and os.path.exists(self.root)

    def get_document(self, doc_uri):
        return self._docs[str(doc_uri)]

    def put_document(self, doc_uri, content):
        path = urlparse(doc_uri).path
        self._check_in_workspace(path)
        self._docs[str(doc_uri)] = Document(
            doc_uri, content, sys_path=self.syspath_for_path(path)
        )

    def rm_document(self, doc_uri):
        self._docs.pop(doc_uri)

    def syspath_for_path(self, path):
        """Construct a sensible sys path to use for the given file path.

        Since the workspace root may not be the root of the Python project we instead
        append the closest parent directory containing a setup.py file.
        """
        files = self.find_parent_files(path, ['setup.py']) or []
        path = [os.path.dirname(setup_py) for setup_py in files]
        path.extend(sys.path)
        return path

    def find_parent_files(self, path, names):
        """Find files matching the given names relative to the given
        document looking in parent directories until one is found """
        self._check_in_workspace(path)
        curdir = os.path.dirname(path)

        while curdir != os.path.dirname(self.root) and curdir != '/':
            existing = list(
                filter(os.path.exists, [os.path.join(curdir, n) for n in names]))
            if existing:
                return existing
            curdir = os.path.dirname(curdir)

    def _check_in_workspace(self, path):
        if not os.path.commonprefix((self.root, path)):
            raise ValueError("Document %s not in workspace %s" % (path, self.root))


class Document(object):

    def __init__(self, uri, source=None, local=True, sys_path=None):
        self.uri = uri
        self.path = urlparse(uri).path
        self.filename = os.path.basename(self.path)
        self.source = source

        if self.source is None:
            with open(self.path, 'r') as f:
                self.source = f.read()

        self._local = local
        self._sys_path = sys_path or sys.path

    def __str__(self):
        return str(self.uri)

    @property
    def lines(self):
        return self.source.splitlines(True)

    def word_at_position(self, position):
        """ Get the word under the cursor returning the start and end positions """
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

    def jedi_names(self):
        return jedi.api.names(source=self.source)

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
    parts[2] = path
    return urlunparse([str(p) for p in parts])
