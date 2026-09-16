# Copyright 2017 Palantir Technologies, Inc.
from test.fixtures import DOC_URI, DOC
import os

try:
    from unittest import mock
except ImportError:
    import mock

import jedi
import pytest

from pyls import uris
from pyls.workspace import Document


def test_document_props(doc):
    assert doc.uri == DOC_URI
    assert doc.source == DOC


def test_document_lines(doc):
    assert len(doc.lines) == 4
    assert doc.lines[0] == 'import sys\n'


def test_document_source_unicode(workspace):
    document_mem = Document(DOC_URI, workspace, u'my source')
    document_disk = Document(DOC_URI, workspace)
    assert isinstance(document_mem.source, type(document_disk.source))


def test_offset_at_position(doc):
    assert doc.offset_at_position({'line': 0, 'character': 8}) == 8
    assert doc.offset_at_position({'line': 1, 'character': 5}) == 16
    assert doc.offset_at_position({'line': 2, 'character': 0}) == 12
    assert doc.offset_at_position({'line': 2, 'character': 4}) == 16
    assert doc.offset_at_position({'line': 4, 'character': 0}) == 51


def test_word_at_position(doc):
    """ Return the position under the cursor (or last in line if past the end) """
    # import sys
    assert doc.word_at_position({'line': 0, 'character': 8}) == 'sys'
    # Past end of import sys
    assert doc.word_at_position({'line': 0, 'character': 1000}) == 'sys'
    # Empty line
    assert doc.word_at_position({'line': 1, 'character': 5}) == ''
    # def main():
    assert doc.word_at_position({'line': 2, 'character': 0}) == 'def'
    # Past end of file
    assert doc.word_at_position({'line': 4, 'character': 0}) == ''


def test_document_empty_edit(workspace):
    doc = Document('file:///uri', workspace, u'')
    doc.apply_change({
        'range': {
            'start': {'line': 0, 'character': 0},
            'end': {'line': 0, 'character': 0}
        },
        'text': u'f'
    })
    assert doc.source == u'f'


def test_document_line_edit(workspace):
    doc = Document('file:///uri', workspace, u'itshelloworld')
    doc.apply_change({
        'text': u'goodbye',
        'range': {
            'start': {'line': 0, 'character': 3},
            'end': {'line': 0, 'character': 8}
        }
    })
    assert doc.source == u'itsgoodbyeworld'


def test_document_multiline_edit(workspace):
    old = [
        "def hello(a, b):\n",
        "    print a\n",
        "    print b\n"
    ]
    doc = Document('file:///uri', workspace, u''.join(old))
    doc.apply_change({'text': u'print a, b', 'range': {
        'start': {'line': 1, 'character': 4},
        'end': {'line': 2, 'character': 11}
    }})
    assert doc.lines == [
        "def hello(a, b):\n",
        "    print a, b\n"
    ]


def test_document_end_of_file_edit(workspace):
    old = [
        "print 'a'\n",
        "print 'b'\n"
    ]
    doc = Document('file:///uri', workspace, u''.join(old))
    doc.apply_change({'text': u'o', 'range': {
        'start': {'line': 2, 'character': 0},
        'end': {'line': 2, 'character': 0}
    }})
    assert doc.lines == [
        "print 'a'\n",
        "print 'b'\n",
        "o",
    ]


INMEMORY_URI = 'inmemory://dummy.py'


def test_non_file_document_props(workspace):
    """A document under a non-file scheme still needs a usable name.

    Monaco sends inmemory://dummy.py, which puts the name in the URI authority. That used
    to resolve to an empty path, leaving the document with no filename or module name.
    """
    document = Document(INMEMORY_URI, workspace, u'import sys')
    assert document.uri == INMEMORY_URI
    assert document.path == '/dummy.py'
    assert document.filename == 'dummy.py'
    assert document.dot_path == 'dummy'
    assert document.is_file_backed is False


def test_non_file_document_source(workspace):
    document = Document(INMEMORY_URI, workspace, u'import sys')
    assert document.source == u'import sys'


def test_non_file_document_without_source_raises(workspace):
    """There is no file to fall back to, so say so rather than opening something else."""
    document = Document(INMEMORY_URI, workspace)
    with pytest.raises(ValueError) as excinfo:
        document.source  # pylint: disable=pointless-statement
    assert INMEMORY_URI in str(excinfo.value)


def test_non_file_document_does_not_extend_sys_path(workspace):
    """os.path.dirname of a non-file document is not a directory.

    It previously normalized to '.', which put the server's working directory on the
    module search path for any in-memory document.
    """
    document = Document(INMEMORY_URI, workspace, u'import sys')
    with mock.patch('jedi.Project', wraps=jedi.Project) as project:
        document.jedi_script(use_document_path=True)
        sys_path = project.call_args[1]['sys_path']
    assert os.getcwd() not in sys_path
    assert '/' not in sys_path


def test_file_document_still_extends_sys_path(tmpdir, workspace):
    """The file-backed behaviour is unchanged."""
    subdir = tmpdir.mkdir('sub')
    source_file = subdir.join('real.py')
    source_file.write('x = 1')

    document = Document(uris.from_fs_path(str(source_file)), workspace, u'x = 1')
    assert document.is_file_backed is True
    with mock.patch('jedi.Project', wraps=jedi.Project) as project:
        document.jedi_script(use_document_path=True)
        sys_path = project.call_args[1]['sys_path']
    assert str(subdir) in sys_path


def test_non_file_document_completions(workspace):
    """The case from the issue: completions inside an in-memory document."""
    document = Document(INMEMORY_URI, workspace, u'import sys\nsys.')
    script = document.jedi_script(use_document_path=True)
    completions = [completion.name for completion in script.complete(2, 4)]
    assert 'argv' in completions
