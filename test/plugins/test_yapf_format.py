# Copyright 2017 Palantir Technologies, Inc.
from pyls import uris
from pyls.plugins.yapf_format import pyls_format_document, pyls_format_range
from pyls.workspace import Document

DOC_URI = uris.from_fs_path(__file__)
DOC = """A = [
    'h',   'w',

    'a'
      ]

B = ['h',


'w']
"""

GOOD_DOC = """A = ['hello', 'world']\n"""


def test_format():
    doc = Document(DOC_URI, DOC)
    res = pyls_format_document(doc)

    assert len(res) == 1
    assert res[0]['newText'] == "A = ['h', 'w', 'a']\n\nB = ['h', 'w']\n"


def test_range_format():
    doc = Document(DOC_URI, DOC)

    def_range = {
        'start': {'line': 0, 'character': 0},
        'end': {'line': 4, 'character': 10}
    }
    res = pyls_format_range(doc, def_range)

    assert len(res) == 1

    # Make sure B is still badly formatted
    assert res[0]['newText'] == "A = ['h', 'w', 'a']\n\nB = ['h',\n\n\n'w']\n"


def test_no_change():
    doc = Document(DOC_URI, GOOD_DOC)
    assert not pyls_format_document(doc)
